import textwrap
from enum import Enum
from typing import Generic, Optional, TypeVar, Union

import strawberry
from strawberry.directive import StrawberryDirective
from strawberry.schema.config import StrawberryConfig
from strawberry.schema.name_converter import NameConverter
from strawberry.schema_directive import Location, StrawberrySchemaDirective
from strawberry.types.arguments import StrawberryArgument
from strawberry.types.base import StrawberryObjectDefinition, StrawberryType
from strawberry.types.enum import EnumDefinition, EnumValue
from strawberry.types.field import StrawberryField
from strawberry.types.scalar import ScalarDefinition
from strawberry.types.union import StrawberryUnion


class AppendsNameConverter(NameConverter):
    def __init__(self, suffix: str):
        self.suffix = suffix
        super().__init__(auto_camel_case=True)

    def from_argument(self, argument: StrawberryArgument) -> str:
        return super().from_argument(argument) + self.suffix

    def from_scalar(self, scalar: ScalarDefinition) -> str:
        return super().from_scalar(scalar) + self.suffix

    def from_field(self, field: StrawberryField) -> str:
        return super().from_field(field) + self.suffix

    def from_union(self, union: StrawberryUnion) -> str:
        return super().from_union(union) + self.suffix

    def from_generic(
        self,
        generic_type: StrawberryObjectDefinition,
        types: list[Union[StrawberryType, type]],
    ) -> str:
        return super().from_generic(generic_type, types) + self.suffix

    def from_interface(self, interface: StrawberryObjectDefinition) -> str:
        return super().from_interface(interface) + self.suffix

    def from_directive(
        self, directive: Union[StrawberryDirective, StrawberrySchemaDirective]
    ) -> str:
        return super().from_directive(directive) + self.suffix

    def from_input_object(self, input_type: StrawberryObjectDefinition) -> str:
        return super().from_object(input_type) + self.suffix

    def from_object(self, object_type: StrawberryObjectDefinition) -> str:
        return super().from_object(object_type) + self.suffix

    def from_enum(self, enum: EnumDefinition) -> str:
        return super().from_enum(enum) + self.suffix

    def from_enum_value(self, enum: EnumDefinition, enum_value: EnumValue) -> str:
        return super().from_enum_value(enum, enum_value) + self.suffix


# TODO: maybe we should have a kitchen sink schema that we can reuse for tests

T = TypeVar("T")

MyScalar = strawberry.scalar(str, name="SensitiveConfiguration")


@strawberry.enum
class MyEnum(Enum):
    A = "a"
    B = "b"


@strawberry.type
class User:
    name: str


@strawberry.type
class Error:
    message: str


@strawberry.input
class UserInput:
    name: str


@strawberry.schema_directive(
    locations=[
        Location.FIELD_DEFINITION,
    ]
)
class MyDirective:
    name: str


@strawberry.interface
class Node:
    id: strawberry.ID


@strawberry.type
class MyGeneric(Generic[T]):
    value: T


@strawberry.type
class Query:
    @strawberry.field(directives=[MyDirective(name="my-directive")])
    def user(self, input: UserInput) -> Union[User, Error]:
        return User(name="Patrick")

    enum: MyEnum = MyEnum.A
    field: Optional[MyGeneric[str]] = None

    @strawberry.field
    def print(self, enum: MyEnum) -> str:
        return enum.value


schema = strawberry.Schema(
    query=Query,
    types=[MyScalar, Node],
    config=StrawberryConfig(name_converter=AppendsNameConverter("X")),
)


def test_name_converter():
    expected_schema = """
    directive @myDirectiveX(name: String!) on FIELD_DEFINITION

    type ErrorX {
      messageX: String!
    }

    enum MyEnumX {
      AX
      BX
    }

    interface NodeXX {
      idX: ID!
    }

    type QueryX {
      enumX: MyEnumX!
      fieldX: StrMyGenericXX
      userX(inputX: UserInputX!): UserXErrorXX! @myDirectiveX(name: "my-directive")
      printX(enumX: MyEnumX!): String!
    }

    scalar SensitiveConfiguration

    type StrMyGenericXX {
      valueX: String!
    }

    input UserInputX {
      nameX: String!
    }

    type UserX {
      nameX: String!
    }

    union UserXErrorXX = UserX | ErrorX
    """

    assert textwrap.dedent(expected_schema).strip() == str(schema)


def test_returns_enum_with_correct_value():
    query = " { enumX } "

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors

    assert result.data == {"enumX": "AX"}


def test_can_use_enum_value():
    query = " { printX(enumX: AX) } "

    result = schema.execute_sync(query, root_value=Query())

    assert not result.errors

    assert result.data == {"printX": "a"}


def test_can_use_enum_value_with_variable():
    query = " query ($enum: MyEnumX!) { printX(enumX: $enum) } "

    result = schema.execute_sync(
        query, root_value=Query(), variable_values={"enum": "AX"}
    )

    assert not result.errors

    assert result.data == {"printX": "a"}
