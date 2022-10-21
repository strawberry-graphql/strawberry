import textwrap
from enum import Enum
from typing import List

from graphql import DirectiveLocation

import strawberry
from strawberry.description_sources import DescriptionSources
from strawberry.schema.config import StrawberryConfig
from strawberry.schema_directive import Location


""" A large example that uses docstrings in all types of GraphQL objects """


@strawberry.schema_directive(locations=[Location.OBJECT, Location.INPUT_OBJECT])
class Keys:
    """
    Identifies the fields that can be used as primary keys

    Attributes:
        fields: Names of the fields used as primary keys
    """

    fields: List[str]


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
    ROCKY_ROAD = "rocky_road"
    """Chocolate ice cream with nuts and marshmallows"""


@strawberry.interface
class InterfaceType:
    """
    This is a graphQL interface type

    Attributes:
        var_a (int): A field that doesn't need a resolver
        var_b (int): A complex field with a resolver
    """

    var_a: int

    @strawberry.field
    def var_b(self, documented: int = 1, undocumented: str = "2") -> str:
        """
        A complex field with a resolver and args

        Args:
            documented (int): Something
        """
        return ""


@strawberry.type(directives=[Keys(fields=["var_f"])])
class ObjectType(InterfaceType):
    """
    This is a graphQL object type

    Attributes:
        var_c (str): Something to differentiate ObjectType from InterfaceType
        var_d:
    """

    var_c: EnumType
    var_d: float  # Empty description is ignored
    var_e: int  # No description
    var_f: str
    """ PEP 257 description """


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


def test_docstrings_disabled():
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        directives=[replace],
        config=StrawberryConfig(description_sources=DescriptionSources.NONE),
    )

    expected = """
        directive @keys(fields: [String!]!) on OBJECT | INPUT_OBJECT

        directive @replace(oldChar: String!, newChar: String!) on FIELD

        enum EnumType {
          VANILLA
          STRAWBERRY
          CHOCOLATE
          ROCKY_ROAD
        }

        input InputType {
          varA: Int!
        }

        interface InterfaceType {
          varA: Int!
          varB(documented: Int! = 1, undocumented: String! = "2"): String!
        }

        type Mutation {
          setObject(newData: InputType!, undocumented: String!): String!
        }

        type ObjectType implements InterfaceType @keys(fields: ["var_f"]) {
          varA: Int!
          varB(documented: Int! = 1, undocumented: String! = "2"): String!
          varC: EnumType!
          varD: Float!
          varE: Int!
          varF: String!
        }

        type Query {
          object: ObjectType!
        }
    """
    assert str(schema) == textwrap.dedent(expected).strip()


def test_class_docstrings():
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        directives=[replace],
        config=StrawberryConfig(
            description_sources=DescriptionSources.CLASS_DOCSTRINGS
        ),
    )

    expected = '''
        """Identifies the fields that can be used as primary keys"""
        directive @keys(
          """Names of the fields used as primary keys"""
          fields: [String!]!
        ) on OBJECT | INPUT_OBJECT

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
          ROCKY_ROAD
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
          """A field that doesn't need a resolver"""
          varA: Int!

          """A complex field with a resolver"""
          varB(documented: Int! = 1, undocumented: String! = "2"): String!
        }

        """Main entrypoint to the GraphQL updates"""
        type Mutation {
          """A GraphQL object"""
          setObject(newData: InputType!, undocumented: String!): String!
        }

        """This is a graphQL object type"""
        type ObjectType implements InterfaceType @keys(fields: ["var_f"]) {
          """A field that doesn't need a resolver"""
          varA: Int!

          """A complex field with a resolver"""
          varB(documented: Int! = 1, undocumented: String! = "2"): String!

          """Something to differentiate ObjectType from InterfaceType"""
          varC: EnumType!
          varD: Float!
          varE: Int!
          varF: String!
        }

        """Main entrypoint to the GraphQL reads"""
        type Query {
          """A GraphQL object"""
          object: ObjectType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_resolver_docstrings():
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        directives=[replace],
        config=StrawberryConfig(
            description_sources=DescriptionSources.RESOLVER_DOCSTRINGS
        ),
    )

    expected = '''
        directive @keys(fields: [String!]!) on OBJECT | INPUT_OBJECT

        directive @replace(oldChar: String!, newChar: String!) on FIELD

        enum EnumType {
          VANILLA
          STRAWBERRY
          CHOCOLATE
          ROCKY_ROAD
        }

        input InputType {
          varA: Int!
        }

        interface InterfaceType {
          varA: Int!

          """A complex field with a resolver and args"""
          varB(
            """Something"""
            documented: Int! = 1
            undocumented: String! = "2"
          ): String!
        }

        type Mutation {
          """Update the object"""
          setObject(
            """New data"""
            newData: InputType!
            undocumented: String!
          ): String!
        }

        type ObjectType implements InterfaceType @keys(fields: ["var_f"]) {
          varA: Int!

          """A complex field with a resolver and args"""
          varB(
            """Something"""
            documented: Int! = 1
            undocumented: String! = "2"
          ): String!
          varC: EnumType!
          varD: Float!
          varE: Int!
          varF: String!
        }

        type Query {
          object: ObjectType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_attribute_docstrings():
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        directives=[replace],
        config=StrawberryConfig(
            description_sources=DescriptionSources.ATTRIBUTE_DOCSTRINGS
        ),
    )

    expected = '''
        directive @keys(fields: [String!]!) on OBJECT | INPUT_OBJECT

        directive @replace(oldChar: String!, newChar: String!) on FIELD

        enum EnumType {
          VANILLA
          STRAWBERRY
          CHOCOLATE

          """Chocolate ice cream with nuts and marshmallows"""
          ROCKY_ROAD
        }

        input InputType {
          varA: Int!
        }

        interface InterfaceType {
          varA: Int!
          varB(documented: Int! = 1, undocumented: String! = "2"): String!
        }

        type Mutation {
          setObject(newData: InputType!, undocumented: String!): String!
        }

        type ObjectType implements InterfaceType @keys(fields: ["var_f"]) {
          varA: Int!
          varB(documented: Int! = 1, undocumented: String! = "2"): String!
          varC: EnumType!
          varD: Float!
          varE: Int!

          """PEP 257 description"""
          varF: String!
        }

        type Query {
          object: ObjectType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_all_docstrings():
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        directives=[replace],
        config=StrawberryConfig(
            description_sources=DescriptionSources.RESOLVER_DOCSTRINGS
            | DescriptionSources.ALL_DOCSTRINGS
        ),
    )

    expected = '''
        """Identifies the fields that can be used as primary keys"""
        directive @keys(
          """Names of the fields used as primary keys"""
          fields: [String!]!
        ) on OBJECT | INPUT_OBJECT

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

          """Chocolate ice cream with nuts and marshmallows"""
          ROCKY_ROAD
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
          """A field that doesn't need a resolver"""
          varA: Int!

          """A complex field with a resolver and args"""
          varB(
            """Something"""
            documented: Int! = 1
            undocumented: String! = "2"
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
        type ObjectType implements InterfaceType @keys(fields: ["var_f"]) {
          """A field that doesn't need a resolver"""
          varA: Int!

          """A complex field with a resolver and args"""
          varB(
            """Something"""
            documented: Int! = 1
            undocumented: String! = "2"
          ): String!

          """Something to differentiate ObjectType from InterfaceType"""
          varC: EnumType!
          varD: Float!
          varE: Int!

          """PEP 257 description"""
          varF: String!
        }

        """Main entrypoint to the GraphQL reads"""
        type Query {
          """A GraphQL object"""
          object: ObjectType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()
