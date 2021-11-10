from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Union

from typing_extensions import Protocol

from strawberry.utils.str_converters import capitalize_first, to_camel_case

from strawberry.schema_directive import StrawberrySchemaDirective


if TYPE_CHECKING:
    from strawberry.arguments import StrawberryArgument
    from strawberry.custom_scalar import ScalarDefinition
    from strawberry.directive import StrawberryDirective
    from strawberry.enum import EnumDefinition
    from strawberry.field import StrawberryField
    from strawberry.lazy_type import LazyType
    from strawberry.type import StrawberryContainer, StrawberryType
    from strawberry.types.types import TypeDefinition
    from strawberry.union import StrawberryUnion


class HasGraphQLName(Protocol):
    python_name: str
    graphql_name: Optional[str]


@dataclass
class StrawberryConfig:
    auto_camel_case: bool = True

    def get_graphql_name(self, obj: HasGraphQLName) -> str:
        if obj.graphql_name is not None:
            return obj.graphql_name

        assert obj.python_name

        if self.auto_camel_case:
            return to_camel_case(obj.python_name)

        return obj.python_name

    def get_argument_name(self, argument: StrawberryArgument) -> str:
        return self.get_graphql_name(argument)

    def get_object_type_name(self, object_type: TypeDefinition) -> str:
        if object_type.concrete_of:
            return self.get_name_from_types(
                object_type.name, list(object_type.type_var_map.values())
            )

        return object_type.name

    def get_input_type_name(self, input_type: TypeDefinition) -> str:
        return self.get_object_type_name(input_type)

    def get_interface_name(self, interface: TypeDefinition) -> str:
        return interface.name

    def get_enum_name(self, enum: EnumDefinition) -> str:
        return enum.name

    def get_directive_name(self, directive: Union[StrawberryDirective, StrawberrySchemaDirective]) -> str:
        name = self.get_graphql_name(directive)

        if self.auto_camel_case:
            # we don't want the first letter to be uppercase for directives
            return name[0].lower() + name[1:]

        return name

    def get_scalar_name(self, scalar: ScalarDefinition) -> str:
        return scalar.name

    def get_field_name(self, field: StrawberryField) -> str:
        return self.get_graphql_name(field)

    def get_union_name(self, union: StrawberryUnion) -> str:
        if union.name is not None:
            return union.name

        name = ""

        for type_ in union.types:
            if hasattr(type_, "_type_definition"):
                name += self.get_object_type_name(type_._type_definition)  # type: ignore
            else:
                name += type.__name__

        return name

    def get_name_from_types(
        self, type_name: str, types: List[Union[StrawberryType, type]]
    ) -> str:
        names: List[str] = []

        for type_ in reversed(types):
            name = self.get_name_from_type(type_)
            names.append(name)

        # we want to generate types from inside out, for example
        # getting `ValueOptionalListStr` from `Value[Optional[List[str]]]`
        # so we reverse the list of names, since it goes outside in
        return type_name + "".join(reversed(names))

    def get_name_from_type(self, type_: Union[StrawberryType, type]) -> str:
        from strawberry.union import StrawberryUnion

        if isinstance(type_, LazyType):
            return type_.type_name
        elif isinstance(type_, EnumDefinition):
            return type_.name
        elif isinstance(type_, StrawberryUnion):
            # TODO: test Generics with unnamed unions
            assert type_.name

            return type_.name
        elif isinstance(type_, StrawberryContainer):
            return type_.name + self.get_name_from_type(type_.of_type)
        elif hasattr(type_, "_type_definition"):
            field_type = type_._type_definition  # type: ignore

            return capitalize_first(field_type.name)
        else:
            return capitalize_first(type_.__name__)  # type: ignore
