from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List, Optional, Sequence, Type

from strawberry.types.types import StrawberryObjectDefinition

if TYPE_CHECKING:
    from dataclasses import Field

    from graphql import GraphQLAbstractType, GraphQLResolveInfo

    from strawberry.field import StrawberryField
    from strawberry.type import WithStrawberryObjectDefinition


class TypeExtension:
    def before_wrap_dataclass(self, cls: Type) -> None:
        pass

    def on_field(self, field: Field | StrawberryField) -> Any:
        return field

    def create_object_definition(
        self,
        origin: Type[Any],
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
        """Posibility to use custom StrawberryObjectDefinition"""

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

    def after_process(self, cls: Type[WithStrawberryObjectDefinition]) -> None:
        pass
