from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Iterator, List, Optional, Sequence

from strawberry.types.types import StrawberryObjectDefinition

if TYPE_CHECKING:
    from dataclasses import Field

    from graphql import GraphQLAbstractType, GraphQLResolveInfo

    from strawberry.field import StrawberryField


class TypeExtension:
    def on_wrap_dataclass(self, cls: type[Any]) -> Iterator[None]:
        "Called before and after strawberry wrapping process"
        yield None

    def on_field(self, field: Field[Any]) -> Field[Any]:
        """Called for each field, _MUST_ return valid field"""
        return field

    def create_object_definition(
        self,
        origin: type[Any],
        name: str,
        is_input: bool,
        is_interface: bool,
        interfaces: List[StrawberryObjectDefinition],
        description: Optional[str],
        directives: Optional[Sequence[object]],
        extend: bool,
        fields: List[StrawberryField],
        is_type_of: Optional[Callable[[Any, GraphQLResolveInfo], bool]],
        resolve_type: Optional[
            Callable[[Any, GraphQLResolveInfo, GraphQLAbstractType], str]
        ],
    ) -> StrawberryObjectDefinition:
        """Hook for creation of StrawberryObjectDefinition for __strawberry_definition__ attr"""

        return StrawberryObjectDefinition(
            name=name,
            is_input=is_input,
            is_interface=is_interface,
            interfaces=interfaces,
            description=description,
            directives=directives,
            origin=origin,
            extend=extend,
            fields=fields,
            is_type_of=is_type_of,
            resolve_type=resolve_type,
        )
