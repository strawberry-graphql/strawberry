from __future__ import annotations

import dataclasses
from functools import cached_property
from typing import TYPE_CHECKING, Any, Callable, Generic, List, Optional, TypeVar
from typing_extensions import Annotated

from graphql import DirectiveLocation

from strawberry.types.field import StrawberryField
from strawberry.types.fields.resolver import (
    INFO_PARAMSPEC,
    ReservedType,
    StrawberryResolver,
)
from strawberry.types.unset import UNSET

if TYPE_CHECKING:
    import inspect

    from strawberry.types.arguments import StrawberryArgument


# TODO: should this be directive argument?
def directive_field(
    name: str,
    default: object = UNSET,
) -> Any:
    """Function to add metadata to a directive argument, like the GraphQL name.

    Args:
        name: The GraphQL name of the directive argument
        default: The default value of the argument

    Returns:
        A StrawberryField object that can be used to customise a directive argument

    Example:
    ```python
    import strawberry
    from strawberry.schema_directive import Location


    @strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
    class Sensitive:
        reason: str = strawberry.directive_field(name="as")
    ```
    """
    return StrawberryField(
        python_name=None,
        graphql_name=name,
        default=default,
    )


T = TypeVar("T")


class StrawberryDirectiveValue: ...


DirectiveValue = Annotated[T, StrawberryDirectiveValue()]
DirectiveValue.__doc__ = (
    """Represents the ``value`` argument for a GraphQL query directive."""
)

# Registers `DirectiveValue[...]` annotated arguments as reserved
VALUE_PARAMSPEC = ReservedType(name="value", type=StrawberryDirectiveValue)


class StrawberryDirectiveResolver(StrawberryResolver[T]):
    RESERVED_PARAMSPEC = (
        INFO_PARAMSPEC,
        VALUE_PARAMSPEC,
    )

    @cached_property
    def value_parameter(self) -> Optional[inspect.Parameter]:
        return self.reserved_parameters.get(VALUE_PARAMSPEC)


@dataclasses.dataclass
class StrawberryDirective(Generic[T]):
    python_name: str
    graphql_name: Optional[str]
    resolver: StrawberryDirectiveResolver[T]
    locations: List[DirectiveLocation]
    description: Optional[str] = None

    @cached_property
    def arguments(self) -> List[StrawberryArgument]:
        return self.resolver.arguments


def directive(
    *,
    locations: List[DirectiveLocation],
    description: Optional[str] = None,
    name: Optional[str] = None,
) -> Callable[[Callable[..., T]], StrawberryDirective[T]]:
    """Decorator to create a GraphQL operation directive.

    Args:
        locations: The locations where the directive can be used
        description: The GraphQL description of the directive
        name: The GraphQL name of the directive

    Returns:
        A StrawberryDirective object that can be used to customise a directive

    Example:
    ```python
    import strawberry
    from strawberry.directive import DirectiveLocation


    @strawberry.directive(
        locations=[DirectiveLocation.FIELD], description="Make string uppercase"
    )
    def turn_uppercase(value: str):
        return value.upper()
    ```
    """

    def _wrap(f: Callable[..., T]) -> StrawberryDirective[T]:
        return StrawberryDirective(
            python_name=f.__name__,
            graphql_name=name,
            locations=locations,
            description=description,
            resolver=StrawberryDirectiveResolver(f),
        )

    return _wrap


__all__ = ["DirectiveLocation", "StrawberryDirective", "directive"]
