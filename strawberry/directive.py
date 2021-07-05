import dataclasses
import inspect
from itertools import islice
from typing import Callable, List, Optional

from graphql import DirectiveLocation

from strawberry.arguments import StrawberryArgument, get_arguments_from_annotations
from strawberry.utils.str_converters import to_camel_case


@dataclasses.dataclass
class DirectiveDefinition:
    name: str
    resolver: Callable
    locations: List[DirectiveLocation]
    description: Optional[str] = None

    @property
    def arguments(self) -> List[StrawberryArgument]:
        annotations = self.resolver.__annotations__
        annotations = dict(islice(annotations.items(), 1, None))
        annotations.pop("return", None)

        parameters = inspect.signature(self.resolver).parameters

        return get_arguments_from_annotations(
            annotations, parameters, origin=self.resolver
        )


def directive(*, locations: List[DirectiveLocation], description=None, name=None):
    def _wrap(f):
        directive_name = name or to_camel_case(f.__name__)

        f.directive_definition = DirectiveDefinition(
            name=directive_name,
            locations=locations,
            description=description,
            resolver=f,
        )

        return f

    return _wrap


__all__ = ["DirectiveLocation", "DirectiveDefinition", "directive"]
