import dataclasses
from typing import Callable, List, Optional

from graphql import DirectiveLocation

from .utils.str_converters import to_camel_case


@dataclasses.dataclass
class DirectiveDefinition:
    name: str
    resolver: Callable
    locations: List[DirectiveLocation]
    description: Optional[str] = None


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
