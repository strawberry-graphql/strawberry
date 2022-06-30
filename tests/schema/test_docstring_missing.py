import textwrap
from enum import Enum

from graphql import DirectiveLocation

import strawberry
from strawberry.description_sources import DescriptionSources
from strawberry.schema.config import StrawberryConfig
from strawberry.schema_directive import Location


"""
dataclasses and other transformations automatically
created a __doc__ if none is provided.

This test ensures we correctly ignore it by retrieving the __doc__ before
calling `wrap_dataclass`
"""


def test_undocumented():
    @strawberry.schema_directive(locations=[Location.OBJECT, Location.INPUT_OBJECT])
    class SchemaDirective:
        name: str

    @strawberry.directive(locations=[DirectiveLocation.FIELD])
    def directive(value: str, old_char: str, new_char: str):
        return value.replace(old_char, new_char)

    @strawberry.enum
    class EnumType(Enum):
        A = "a"

    @strawberry.interface
    class InterfaceType:
        var_a: EnumType

    @strawberry.type
    class ObjectType(InterfaceType):
        var_b: EnumType

    @strawberry.input
    class InputType:
        var_b: EnumType

    @strawberry.type(directives=[SchemaDirective(name="name")])
    class Query:
        obj: ObjectType

        @strawberry.field
        def resolver(self, input: InputType) -> ObjectType:
            pass

    schema = strawberry.Schema(
        query=Query,
        directives=[directive],
        config=StrawberryConfig(description_sources=DescriptionSources.ALL),
    )

    expected = '''
        directive @schemaDirective(name: String!) on OBJECT | INPUT_OBJECT

        directive @directive(oldChar: String!, newChar: String!) on FIELD

        """An enumeration."""
        enum EnumType {
          A
        }

        input InputType {
          varB: EnumType!
        }

        interface InterfaceType {
          varA: EnumType!
        }

        type ObjectType implements InterfaceType {
          varA: EnumType!
          varB: EnumType!
        }

        type Query @schemaDirective(name: "name") {
          obj: ObjectType!
          resolver(input: InputType!): ObjectType!
        }
    '''

    assert str(schema) == textwrap.dedent(expected).strip()
