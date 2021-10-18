from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from typing_extensions import Protocol

from strawberry.extensions import Extension
from strawberry.types.info import Info
from strawberry.utils.await_maybe import await_maybe


if TYPE_CHECKING:

    from strawberry.schema.schema import Schema


SPECIFIED_DIRECTIVES = {"include", "skip"}


class Middleware(Protocol):
    @abstractmethod
    def resolve(self, next_, root, info: Info, **kwargs) -> None:
        raise NotImplementedError


class DirectivesExtension(Extension):
    async def resolve(self, next_, root, info, **kwargs) -> Any:
        result = await await_maybe(next_(root, info, **kwargs))

        for directive in info.field_nodes[0].directives:
            directive_name = directive.name.value

            if directive_name in SPECIFIED_DIRECTIVES:
                continue

            # TODO: support converting lists
            arguments = {
                argument.name.value: argument.value.value
                for argument in directive.arguments
            }

            schema: Schema = info.schema._strawberry_schema
            strawberry_directive = schema.get_directive_by_name(directive_name)
            assert (
                strawberry_directive is not None
            ), f"Directive {directive_name} not found"

            result = await await_maybe(
                strawberry_directive.resolver(result, **arguments)
            )

        return result


class DirectivesExtensionSync(Extension):
    # TODO: we might need the graphql info here
    def resolve(self, next_, root, info, **kwargs) -> Any:
        result = next_(root, info, **kwargs)

        for directive in info.field_nodes[0].directives:
            directive_name = directive.name.value

            if directive_name in SPECIFIED_DIRECTIVES:
                continue

            # TODO: support converting lists
            arguments = {
                argument.name.value: argument.value.value
                for argument in directive.arguments
            }

            schema: Schema = info.schema._strawberry_schema
            strawberry_directive = schema.get_directive_by_name(directive_name)
            assert (
                strawberry_directive is not None
            ), f"Directive {directive_name} not found"

            result = strawberry_directive.resolver(result, **arguments)

        return result
