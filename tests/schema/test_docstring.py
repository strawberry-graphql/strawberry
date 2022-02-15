import textwrap
from enum import Enum

from graphql import DirectiveLocation

import strawberry
from strawberry.schema.config import StrawberryConfig


@strawberry.directive(locations=[DirectiveLocation.FIELD])
def replace(value: str, old_char: str, new_char: str):
    """
    Replaces a character in the string

    Args:
        value: String being edited
        old_char: Character being removed
        new_char: Character being added
    """
    return value.replace(old_char, new_char)


@strawberry.enum
class EnumType(Enum):
    """
    Enum type description

    Attributes:
        VANILLA: Vanilla is a spice derived from orchids of the genus Vanilla
        STRAWBERRY: The garden strawberry is a widely grown species of the genus Fragaria
        CHOCOLATE: Chocolate is a food product made from roasted and ground cacao pods
    """

    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"


@strawberry.interface
class InterfaceType:
    """
    This is a graphQL interface type

    Attributes:
        var_a (int): A fields that doesn't need a resolver
        var_b (int): A complex field with a resolver
    """

    var_a: int

    @strawberry.field
    def var_b(self, arg_1: int = 1, arg_2: str = 2) -> str:
        """
        A complex field with a resolver and args

        Args:
            arg_1 (int): Something
            arg_2 (str): Another thing
        """
        return ""


@strawberry.type
class ObjectType(InterfaceType):
    """
    This is a graphQL object type

    Attributes:
        var_a (int): A field that doesn't need a resolver
        var_b (int): A complex field with a resolver
        var_c (str): Something to differentiate ObjectType from InterfaceType
    """

    var_c: EnumType


@strawberry.input
class InputType:
    """
    This is a graphQL input type

    Description has many lines.
    Many, many lines

    Attributes:
        var_a (int): Something
    """

    var_a: int


@strawberry.type
class Query:
    """
    Main entrypoint to the GraphQL reads

    Attributes:
        object: A GraphQL object
    """

    object: ObjectType


@strawberry.type
class Mutation:
    """
    Main entrypoint to the GraphQL updates

    Attributes:
        set_object: A GraphQL object
    """

    @strawberry.field
    def set_object(new_data: InputType, undocumented: str) -> str:
        """
        Update the object

        Args:
            new_data: New data
            x-undocumented: This fields won't have a GraphQL description
        """
        return ""


def test_docstrings_enabled():
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        directives=[replace],
        config=StrawberryConfig(description_from_docstrings=True),
    )

    expected = '''
        """Replaces a character in the string"""
        directive @replace(
          """Character being removed"""
          oldChar: String!

          """Character being added"""
          newChar: String!
        ) on FIELD

        """Enum type description"""
        enum EnumType {
          """Vanilla is a spice derived from orchids of the genus Vanilla"""
          VANILLA

          """The garden strawberry is a widely grown species of the genus Fragaria"""
          STRAWBERRY

          """Chocolate is a food product made from roasted and ground cacao pods"""
          CHOCOLATE
        }

        """
        This is a graphQL input type

        Description has many lines.
        Many, many lines
        """
        input InputType {
          """Something"""
          varA: Int!
        }

        """This is a graphQL interface type"""
        interface InterfaceType {
          """A fields that doesn't need a resolver"""
          varA: Int!

          """A complex field with a resolver and args"""
          varB(
            """Something"""
            arg1: Int! = 1

            """Another thing"""
            arg2: String! = "2"
          ): String!
        }

        """Main entrypoint to the GraphQL updates"""
        type Mutation {
          """Update the object"""
          setObject(
            """New data"""
            newData: InputType!
            undocumented: String!
          ): String!
        }

        """This is a graphQL object type"""
        type ObjectType implements InterfaceType {
          """A field that doesn't need a resolver"""
          varA: Int!

          """A complex field with a resolver and args"""
          varB(
            """Something"""
            arg1: Int! = 1

            """Another thing"""
            arg2: String! = "2"
          ): String!

          """Something to differentiate ObjectType from InterfaceType"""
          varC: EnumType!
        }

        """Main entrypoint to the GraphQL reads"""
        type Query {
          """A GraphQL object"""
          object: ObjectType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_docstrings_disabled():
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        directives=[replace],
        config=StrawberryConfig(description_from_docstrings=False),
    )

    expected = """
        directive @replace(oldChar: String!, newChar: String!) on FIELD

        enum EnumType {
          VANILLA
          STRAWBERRY
          CHOCOLATE
        }

        input InputType {
          varA: Int!
        }

        interface InterfaceType {
          varA: Int!
          varB(arg1: Int! = 1, arg2: String! = "2"): String!
        }

        type Mutation {
          setObject(newData: InputType!, undocumented: String!): String!
        }

        type ObjectType implements InterfaceType {
          varA: Int!
          varB(arg1: Int! = 1, arg2: String! = "2"): String!
          varC: EnumType!
        }

        type Query {
          object: ObjectType!
        }
    """
    assert str(schema) == textwrap.dedent(expected).strip()
