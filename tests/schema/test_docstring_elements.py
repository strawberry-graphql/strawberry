import textwrap
from enum import Enum

from typing_extensions import Annotated

from graphql import DirectiveLocation

import strawberry
from strawberry.description_source import DescriptionSource
from strawberry.schema.config import StrawberryConfig
from strawberry.schema_directive import Location


"""
Schema Directive
"""


@strawberry.schema_directive(
    description="SchemaDirective description",
    locations=[Location.OBJECT, Location.INPUT_OBJECT],
)
class SchemaDirective:
    """
    SchemaDirective docstring

    Attributes:
        name1: name1 docstring
        name2: name2 docstring
    """

    name1: Annotated[str, strawberry.argument(description="name1 description")]
    """ name1 attribute docstring """

    name2: str = strawberry.field(description="name2 description")
    """ name2 attribute docstring """


@strawberry.type(
    name="Query", directives=[SchemaDirective(name1="name1", name2="name2")]
)
class SchemaDirectiveQuery:
    Q: int


def test_schema_directive_description():
    schema = strawberry.Schema(
        query=SchemaDirectiveQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.STRAWBERRY_DESCRIPTIONS]
        ),
    )
    expected = '''
        """SchemaDirective description"""
        directive @schemaDirective(
          """name1 description"""
          name1: String!

          """name2 description"""
          name2: String!
        ) on OBJECT | INPUT_OBJECT

        type Query @schemaDirective(name1: "name1", name2: "name2") {
          Q: Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_schema_directive_docstring():
    schema = strawberry.Schema(
        query=SchemaDirectiveQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.DIRECTIVE_DOCSTRINGS]
        ),
    )
    expected = '''
        """SchemaDirective docstring"""
        directive @schemaDirective(
          """name1 docstring"""
          name1: String!

          """name2 docstring"""
          name2: String!
        ) on OBJECT | INPUT_OBJECT

        type Query @schemaDirective(name1: "name1", name2: "name2") {
          Q: Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_schema_directive_attr_docstring():
    schema = strawberry.Schema(
        query=SchemaDirectiveQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.DIRECTIVE_ATTRIBUTE_DOCSTRING]
        ),
    )
    expected = '''
        directive @schemaDirective(
          """name1 attribute docstring"""
          name1: String!

          """name2 attribute docstring"""
          name2: String!
        ) on OBJECT | INPUT_OBJECT

        type Query @schemaDirective(name1: "name1", name2: "name2") {
          Q: Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_schema_directive_others():
    schema = strawberry.Schema(
        query=SchemaDirectiveQuery,
        config=StrawberryConfig(
            description_sources=[
                src
                for src in DescriptionSource
                if src
                not in [
                    DescriptionSource.STRAWBERRY_DESCRIPTIONS,
                    DescriptionSource.DIRECTIVE_DOCSTRINGS,
                    DescriptionSource.DIRECTIVE_ATTRIBUTE_DOCSTRING,
                ]
            ]
        ),
    )
    expected = """
        directive @schemaDirective(name1: String!, name2: String!) on OBJECT | INPUT_OBJECT

        type Query @schemaDirective(name1: "name1", name2: "name2") {
          Q: Int!
        }
    """  # noqa
    assert str(schema) == textwrap.dedent(expected).strip()


"""
Directive
"""


@strawberry.directive(
    description="Directive description", locations=[DirectiveLocation.FIELD]
)
def directive(
    value: str, arg: Annotated[str, strawberry.argument(description="arg description")]
) -> str:
    """
    Directive docstring

    Args:
        arg: arg docstring
    """
    return value


@strawberry.type(name="Query")
class DirectiveQuery:
    Q: str


def test_directive_description():
    schema = strawberry.Schema(
        query=DirectiveQuery,
        directives=[directive],
        config=StrawberryConfig(
            description_sources=[DescriptionSource.STRAWBERRY_DESCRIPTIONS]
        ),
    )
    expected = '''
        """Directive description"""
        directive @directive(
          """arg description"""
          arg: String!
        ) on FIELD

        type Query {
          Q: String!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_directive_docstring():
    schema = strawberry.Schema(
        query=DirectiveQuery,
        directives=[directive],
        config=StrawberryConfig(
            description_sources=[DescriptionSource.DIRECTIVE_DOCSTRINGS]
        ),
    )
    expected = '''
        """Directive docstring"""
        directive @directive(
          """arg docstring"""
          arg: String!
        ) on FIELD

        type Query {
          Q: String!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_directive_others():
    schema = strawberry.Schema(
        query=DirectiveQuery,
        directives=[directive],
        config=StrawberryConfig(
            description_sources=[
                src
                for src in DescriptionSource
                if src
                not in [
                    DescriptionSource.STRAWBERRY_DESCRIPTIONS,
                    DescriptionSource.DIRECTIVE_DOCSTRINGS,
                ]
            ]
        ),
    )
    expected = """
        directive @directive(arg: String!) on FIELD

        type Query {
          Q: String!
        }
    """
    assert str(schema) == textwrap.dedent(expected).strip()


"""
Enum
"""


@strawberry.enum(description="Enum description")
class EnumType(Enum):
    """
    Enum docstring

    Attributes:
        A: A docstring
    """

    A = "A"
    """ A attribute docstring """


@strawberry.type(name="Query")
class EnumQuery:
    Q: EnumType


def test_enum_description():
    schema = strawberry.Schema(
        query=EnumQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.STRAWBERRY_DESCRIPTIONS]
        ),
    )
    expected = '''
        """Enum description"""
        enum EnumType {
          A
        }

        type Query {
          Q: EnumType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_enum_docstring():
    schema = strawberry.Schema(
        query=EnumQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.ENUM_DOCSTRINGS]
        ),
    )
    expected = '''
        """Enum docstring"""
        enum EnumType {
          """A docstring"""
          A
        }

        type Query {
          Q: EnumType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_enum_attr_docstring():
    schema = strawberry.Schema(
        query=EnumQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.ENUM_ATTRIBUTE_DOCSTRING]
        ),
    )
    expected = '''
        enum EnumType {
          """A attribute docstring"""
          A
        }

        type Query {
          Q: EnumType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_enum_others():
    schema = strawberry.Schema(
        query=EnumQuery,
        config=StrawberryConfig(
            description_sources=[
                src
                for src in DescriptionSource
                if src
                not in [
                    DescriptionSource.STRAWBERRY_DESCRIPTIONS,
                    DescriptionSource.ENUM_DOCSTRINGS,
                    DescriptionSource.ENUM_ATTRIBUTE_DOCSTRING,
                ]
            ]
        ),
    )
    expected = """
        enum EnumType {
          A
        }

        type Query {
          Q: EnumType!
        }
    """
    assert str(schema) == textwrap.dedent(expected).strip()


"""
Object
"""


@strawberry.type(description="ObjectType description")
class ObjectType:
    """
    ObjectType docstring

    Attributes:
        A: A docstring
        f: f docstring
    """

    A: int = strawberry.field(description="A description")
    """ A attribute docstring """

    @strawberry.field(description="f description")
    def f(
        self, arg: Annotated[str, strawberry.argument(description="arg description")]
    ) -> int:
        """
        f resolver docstring

        Args:
            arg: arg resolver docstring
        """
        return 1


@strawberry.type(name="Query")
class ObjectQuery:
    Q: ObjectType


def test_object_description():
    schema = strawberry.Schema(
        query=ObjectQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.STRAWBERRY_DESCRIPTIONS]
        ),
    )
    expected = '''
        """ObjectType description"""
        type ObjectType {
          """A description"""
          A: Int!

          """f description"""
          f(
            """arg description"""
            arg: String!
          ): Int!
        }

        type Query {
          Q: ObjectType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_object_docstring():
    schema = strawberry.Schema(
        query=ObjectQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.TYPE_DOCSTRINGS]
        ),
    )
    expected = '''
        """ObjectType docstring"""
        type ObjectType {
          """A docstring"""
          A: Int!

          """f docstring"""
          f(arg: String!): Int!
        }

        type Query {
          Q: ObjectType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_object_attr_docstring():
    schema = strawberry.Schema(
        query=ObjectQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.TYPE_ATTRIBUTE_DOCSTRING]
        ),
    )
    expected = '''
        type ObjectType {
          """A attribute docstring"""
          A: Int!
          f(arg: String!): Int!
        }

        type Query {
          Q: ObjectType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_object_resolver_docstring():
    schema = strawberry.Schema(
        query=ObjectQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.RESOLVER_DOCSTRINGS]
        ),
    )
    expected = '''
        type ObjectType {
          A: Int!

          """f resolver docstring"""
          f(
            """arg resolver docstring"""
            arg: String!
          ): Int!
        }

        type Query {
          Q: ObjectType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_object_resolver_others():
    schema = strawberry.Schema(
        query=ObjectQuery,
        config=StrawberryConfig(
            description_sources=[
                src
                for src in DescriptionSource
                if src
                not in [
                    DescriptionSource.STRAWBERRY_DESCRIPTIONS,
                    DescriptionSource.TYPE_DOCSTRINGS,
                    DescriptionSource.TYPE_ATTRIBUTE_DOCSTRING,
                    DescriptionSource.RESOLVER_DOCSTRINGS,
                ]
            ]
        ),
    )
    expected = """
        type ObjectType {
          A: Int!
          f(arg: String!): Int!
        }

        type Query {
          Q: ObjectType!
        }
    """
    assert str(schema) == textwrap.dedent(expected).strip()


"""
Interface
"""


@strawberry.interface(description="InterfaceType description")
class InterfaceType:
    """
    InterfaceType docstring

    Attributes:
        A: A docstring
        f: f docstring
    """

    A: int = strawberry.field(description="A description")
    """ A attribute docstring """

    @strawberry.field(description="f description")
    def f(
        self, arg: Annotated[str, strawberry.argument(description="arg description")]
    ) -> int:
        """
        f resolver docstring

        Args:
            arg: arg resolver docstring
        """
        return 1


@strawberry.type(name="Query")
class InterfaceQuery(InterfaceType):
    Q: InterfaceType


def test_interface_description():
    schema = strawberry.Schema(
        query=InterfaceQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.STRAWBERRY_DESCRIPTIONS]
        ),
    )
    expected = '''
        """InterfaceType description"""
        interface InterfaceType {
          """A description"""
          A: Int!

          """f description"""
          f(
            """arg description"""
            arg: String!
          ): Int!
        }

        type Query implements InterfaceType {
          """A description"""
          A: Int!

          """f description"""
          f(
            """arg description"""
            arg: String!
          ): Int!
          Q: InterfaceType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_interface_docstring():
    schema = strawberry.Schema(
        query=InterfaceQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.TYPE_DOCSTRINGS]
        ),
    )
    expected = '''
        """InterfaceType docstring"""
        interface InterfaceType {
          """A docstring"""
          A: Int!

          """f docstring"""
          f(arg: String!): Int!
        }

        type Query implements InterfaceType {
          """A docstring"""
          A: Int!

          """f docstring"""
          f(arg: String!): Int!
          Q: InterfaceType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_interface_attr_docstring():
    schema = strawberry.Schema(
        query=InterfaceQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.TYPE_ATTRIBUTE_DOCSTRING]
        ),
    )
    expected = '''
        interface InterfaceType {
          """A attribute docstring"""
          A: Int!
          f(arg: String!): Int!
        }

        type Query implements InterfaceType {
          """A attribute docstring"""
          A: Int!
          f(arg: String!): Int!
          Q: InterfaceType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_interface_resolver_docstring():
    schema = strawberry.Schema(
        query=InterfaceQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.RESOLVER_DOCSTRINGS]
        ),
    )
    expected = '''
        interface InterfaceType {
          A: Int!

          """f resolver docstring"""
          f(
            """arg resolver docstring"""
            arg: String!
          ): Int!
        }

        type Query implements InterfaceType {
          A: Int!

          """f resolver docstring"""
          f(
            """arg resolver docstring"""
            arg: String!
          ): Int!
          Q: InterfaceType!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_interface_others():
    schema = strawberry.Schema(
        query=InterfaceQuery,
        config=StrawberryConfig(
            description_sources=[
                src
                for src in DescriptionSource
                if src
                not in [
                    DescriptionSource.STRAWBERRY_DESCRIPTIONS,
                    DescriptionSource.TYPE_DOCSTRINGS,
                    DescriptionSource.TYPE_ATTRIBUTE_DOCSTRING,
                    DescriptionSource.RESOLVER_DOCSTRINGS,
                ]
            ]
        ),
    )
    expected = """
        interface InterfaceType {
          A: Int!
          f(arg: String!): Int!
        }

        type Query implements InterfaceType {
          A: Int!
          f(arg: String!): Int!
          Q: InterfaceType!
        }
    """
    assert str(schema) == textwrap.dedent(expected).strip()


"""
Input
"""


@strawberry.input(description="InputType description")
class InputType:
    """
    InputType docstring

    Attributes:
        A: A docstring
    """

    A: int = strawberry.field(description="A description")
    """ A attribute docstring """


@strawberry.type(name="Query")
class InputQuery:
    @strawberry.field
    def f(self, input: InputType) -> int:
        return 1


def test_input_description():
    schema = strawberry.Schema(
        query=InputQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.STRAWBERRY_DESCRIPTIONS]
        ),
    )
    expected = '''
        """InputType description"""
        input InputType {
          """A description"""
          A: Int!
        }

        type Query {
          f(input: InputType!): Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_input_docstring():
    schema = strawberry.Schema(
        query=InputQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.TYPE_DOCSTRINGS]
        ),
    )
    expected = '''
        """InputType docstring"""
        input InputType {
          """A docstring"""
          A: Int!
        }

        type Query {
          f(input: InputType!): Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_input_attr_docstring():
    schema = strawberry.Schema(
        query=InputQuery,
        config=StrawberryConfig(
            description_sources=[DescriptionSource.TYPE_ATTRIBUTE_DOCSTRING]
        ),
    )
    expected = '''
        input InputType {
          """A attribute docstring"""
          A: Int!
        }

        type Query {
          f(input: InputType!): Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_input_others():
    schema = strawberry.Schema(
        query=InputQuery,
        config=StrawberryConfig(
            description_sources=[
                src
                for src in DescriptionSource
                if src
                not in [
                    DescriptionSource.STRAWBERRY_DESCRIPTIONS,
                    DescriptionSource.TYPE_DOCSTRINGS,
                    DescriptionSource.TYPE_ATTRIBUTE_DOCSTRING,
                ]
            ]
        ),
    )
    expected = """
        input InputType {
          A: Int!
        }

        type Query {
          f(input: InputType!): Int!
        }
    """
    assert str(schema) == textwrap.dedent(expected).strip()
