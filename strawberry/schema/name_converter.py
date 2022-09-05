from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from typing_extensions import Protocol

from strawberry.custom_scalar import ScalarDefinition
from strawberry.directive import StrawberryDirective
from strawberry.enum import EnumDefinition
from strawberry.lazy_type import LazyType
from strawberry.schema_directive import StrawberrySchemaDirective
from strawberry.type import StrawberryList, StrawberryOptional, StrawberryType
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion
from strawberry.utils.str_converters import capitalize_first, to_camel_case


if TYPE_CHECKING:
    from strawberry.arguments import StrawberryArgument
    from strawberry.field import StrawberryField


class HasGraphQLName(Protocol):
    python_name: str
    graphql_name: Optional[str]


class NameConverter:
    def __init__(self, auto_camel_case: bool = True) -> None:
        self.auto_camel_case = auto_camel_case

    def from_type(
        self,
        type_: Union[StrawberryType, StrawberryDirective, StrawberryDirective],
    ) -> str:
        if isinstance(type_, (StrawberryDirective, StrawberrySchemaDirective)):
            return self.from_directive(type_)
        if isinstance(type_, EnumDefinition):  # TODO: Replace with StrawberryEnum
            return self.from_enum(type_)
        elif isinstance(type_, TypeDefinition):
            if type_.is_input:
                return self.from_input_object(type_)
            if type_.is_interface:
                return self.from_interface(type_)
            return self.from_object(type_)
        elif isinstance(type_, StrawberryUnion):
            return self.from_union(type_)
        elif isinstance(type_, ScalarDefinition):  # TODO: Replace with StrawberryScalar
            return self.from_scalar(type_)

        raise TypeError(f"Unexpected type '{type_}'")

    def from_argument(self, argument: StrawberryArgument) -> str:
        return self.get_graphql_name(argument)

    def from_object(self, object_type: TypeDefinition) -> str:
        if object_type.concrete_of:
            return self.from_generic(
                object_type, list(object_type.type_var_map.values())
            )

        return object_type.name

    def from_input_object(self, input_type: TypeDefinition) -> str:
        return self.from_object(input_type)

    def from_interface(self, interface: TypeDefinition) -> str:
        return self.from_object(interface)

    def from_enum(self, enum: EnumDefinition) -> str:
        return enum.name

    def from_directive(
        self, directive: Union[StrawberryDirective, StrawberrySchemaDirective]
    ) -> str:
        name = self.get_graphql_name(directive)

        if self.auto_camel_case:
            # we don't want the first letter to be uppercase for directives
            return name[0].lower() + name[1:]

        return name

    def from_scalar(self, scalar: ScalarDefinition) -> str:
        return scalar.name

    def from_field(self, field: StrawberryField) -> str:
        return self.get_graphql_name(field)

    def from_union(self, union: StrawberryUnion) -> str:
        if union.graphql_name is not None:
            return union.graphql_name

        name = ""

        for type_ in union.types:
            assert hasattr(type_, "_type_definition")
            name += self.from_type(type_._type_definition)  # type: ignore

        return name

    def from_generic(
        self, generic_type: TypeDefinition, types: List[Union[StrawberryType, type]]
    ) -> str:
        generic_type_name = generic_type.name

        names: List[str] = []

        for type_ in types:
            name = self.get_from_type(type_)
            names.append(name)

        return "".join(names) + generic_type_name

    def get_from_type(self, type_: Union[StrawberryType, type]) -> str:
        from strawberry.union import StrawberryUnion

        if isinstance(type_, LazyType):
            name = type_.type_name
        elif isinstance(type_, EnumDefinition):
            name = type_.name
        elif isinstance(type_, StrawberryUnion):
            # TODO: test Generics with unnamed unions
            assert type_.graphql_name

            name = type_.graphql_name
        elif isinstance(type_, StrawberryList):
            name = self.get_from_type(type_.of_type) + "List"
        elif isinstance(type_, StrawberryOptional):
            name = self.get_from_type(type_.of_type) + "Optional"
        elif hasattr(type_, "_scalar_definition"):
            strawberry_type = type_._scalar_definition  # type: ignore

            name = strawberry_type.name
        elif hasattr(type_, "_type_definition"):
            strawberry_type = type_._type_definition  # type: ignore

            if strawberry_type.is_generic:
                types = type_.__args__  # type: ignore
                name = self.from_generic(strawberry_type, types)
            elif strawberry_type.concrete_of:
                types = list(strawberry_type.type_var_map.values())
                name = self.from_generic(strawberry_type, types)
            else:
                name = strawberry_type.name
        else:
            name = type_.__name__  # type: ignore

        return capitalize_first(name)

    def get_graphql_name(self, obj: HasGraphQLName) -> str:
        if obj.graphql_name is not None:
            return obj.graphql_name

        assert obj.python_name

        if self.auto_camel_case:
            return to_camel_case(obj.python_name)

        return obj.python_name
