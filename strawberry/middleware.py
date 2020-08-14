from abc import abstractmethod
from typing import Any, Dict, List

from typing_extensions import Protocol

from .directive import DirectiveDefinition


SPECIFIED_DIRECTIVES = {"include", "skip"}


class Middleware(Protocol):
    @abstractmethod
    def resolve(self, next_, root, info, **kwargs):
        raise NotImplementedError


class DirectivesMiddleware:
    def __init__(self, directives: List[Any]):
        self.directives: Dict[str, DirectiveDefinition] = {
            directive.directive_definition.name: directive.directive_definition
            for directive in directives
        }

    def resolve(self, next_, root, info, **kwargs):
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
