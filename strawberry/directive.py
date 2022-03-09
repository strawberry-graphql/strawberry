from __future__ import annotations

import dataclasses
import inspect
from typing import Callable, List, Optional, TypeVar

from backports.cached_property import cached_property
from typing_extensions import Annotated

from graphql import DirectiveLocation

from strawberry.arguments import StrawberryArgument
from strawberry.types.fields.resolver import (
    INFO_PARAMSPEC,
    ROOT_PARAMSPEC,
    ReservedType,
    StrawberryResolver,
)


T = TypeVar("T")


class StrawberryDirectiveValue:
    ...


DirectiveValue = Annotated[T, StrawberryDirectiveValue()]
DirectiveValue.__doc__ = (
    """Represents the ``value`` argument for a GraphQL query directive."""
)


VALUE_PARAMSPEC = ReservedType(name="value", type=StrawberryDirectiveValue)
"""Registers `DirectiveValue[...]` annotated arguments as reserved."""


class StrawberryDirectiveResolver(StrawberryResolver[T]):

    RESERVED_PARAMSPEC = (
        INFO_PARAMSPEC,
        ROOT_PARAMSPEC,
        VALUE_PARAMSPEC,
    )

    @cached_property
    def value_parameter(self) -> Optional[inspect.Parameter]:
        return self.reserved_parameters.get(VALUE_PARAMSPEC)


@dataclasses.dataclass
class StrawberryDirective:
    python_name: str
    graphql_name: Optional[str]
    resolver: StrawberryDirectiveResolver
    locations: List[DirectiveLocation]
    description: Optional[str] = None

    @property
    def arguments(self) -> List[StrawberryArgument]:
        return self.resolver.arguments


def directive(
    *,
    locations: List[DirectiveLocation],
    description: Optional[str] = None,
    name: Optional[str] = None,
) -> Callable[[Callable[..., T]], T]:
    def _wrap(f: Callable[..., T]) -> T:
        return StrawberryDirective(  # type: ignore
            python_name=f.__name__,
            graphql_name=name,
            locations=locations,
            description=description,
            resolver=StrawberryDirectiveResolver(f),
        )

    return _wrap


__all__ = ["DirectiveLocation", "StrawberryDirective", "directive"]
