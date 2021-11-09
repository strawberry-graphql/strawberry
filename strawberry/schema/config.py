from dataclasses import dataclass

from strawberry.arguments import StrawberryArgument
from strawberry.custom_scalar import ScalarDefinition
from strawberry.directive import StrawberryDirective
from strawberry.enum import EnumDefinition
from strawberry.types.types import TypeDefinition
from strawberry.union import StrawberryUnion


@dataclass
class StrawberryConfig:
    auto_camel_case: bool = True

    def get_argument_name(self, argument: StrawberryArgument) -> str:
        return argument.get_graphql_name(self.auto_camel_case)

    def get_object_type_name(self, object_type: TypeDefinition) -> str:
        return object_type.name

    def get_input_type_name(self, input_type: TypeDefinition) -> str:
        return input_type.name

    def get_interface_name(self, interface: TypeDefinition) -> str:
        return interface.name

    def get_enum_name(self, enum: EnumDefinition) -> str:
        return enum.name

    def get_directive_name(self, directive: StrawberryDirective) -> str:
        return directive.get_graphql_name(self.auto_camel_case)

    def get_scalar_name(self, scalar: ScalarDefinition) -> str:
        return scalar.name

    def get_union_name(self, union: StrawberryUnion) -> str:
        return union.name
