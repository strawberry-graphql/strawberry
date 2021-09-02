from abc import abstractmethod
from typing import Any, Dict, Sequence

from typing_extensions import Protocol

from strawberry.types.info import Info
from strawberry.utils.await_maybe import await_maybe

from .directive import StrawberryDirective


SPECIFIED_DIRECTIVES = {"include", "skip"}


class Middleware(Protocol):
    @abstractmethod
    def resolve(self, next_, root, info: Info, **kwargs) -> None:
        raise NotImplementedError


class DirectivesMiddlewareBase:
    def __init__(self, directives: Sequence[StrawberryDirective]):
        self.directives: Dict[str, StrawberryDirective] = {
            directive.graphql_name: directive for directive in directives
        }


class DirectivesMiddleware(DirectivesMiddlewareBase):
    # TODO: we might need the graphql info here
    async def resolve(self, next_, root, info, **kwargs) -> Any:
        result = await await_maybe(next_(root, info, **kwargs))

        for directive in info.field_nodes[0].directives:
            directive_name = directive.name.value

            if directive_name in SPECIFIED_DIRECTIVES:
                continue

            func = self.directives[directive_name].resolver

            # TODO: support converting lists

            arguments = {
                argument.name.value: argument.value.value
                for argument in directive.arguments
            }

            result = await await_maybe(func(result, **arguments))

        return result


class DirectivesMiddlewareSync(DirectivesMiddlewareBase):
    # TODO: we might need the graphql info here
    def resolve(self, next_, root, info, **kwargs) -> Any:
        result = next_(root, info, **kwargs)

        for directive in info.field_nodes[0].directives:
            directive_name = directive.name.value

            if directive_name in SPECIFIED_DIRECTIVES:
                continue

            func = self.directives[directive_name].resolver

            # TODO: support converting lists

            arguments = {
                argument.name.value: argument.value.value
                for argument in directive.arguments
            }

            result = func(result, **arguments)

        return result
