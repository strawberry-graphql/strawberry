import textwrap

import strawberry
from strawberry.description_sources import DescriptionSources
from strawberry.schema.config import StrawberryConfig


@strawberry.type(description="A description")
class A:
    """
    A docstring

    Attributes:
        a: a docstring
        b: b docstring
        c: c docstring
        d: d docstring
        e: e docstring

        f1: f1 docstring
        f2: f2 docstring
        f3: f3 docstring
        f4: f4 docstring
        f5: f5 docstring
    """

    a: int = strawberry.field(description="a description")
    """ a attribute docstring """
    b: int = strawberry.field(
        description="b description",
        description_sources=DescriptionSources.STRAWBERRY_DESCRIPTIONS,
    )
    """ b attribute docstring """
    c: int = strawberry.field(
        description="c description",
        description_sources=DescriptionSources.TYPE_DOCSTRINGS,
    )
    """ c attribute docstring """
    d: int = strawberry.field(
        description="d description",
        description_sources=DescriptionSources.TYPE_ATTRIBUTE_DOCSTRINGS,
    )
    """ d attribute docstring """
    e: int = strawberry.field(
        description="e description", description_sources=DescriptionSources.NONE
    )
    """ d attribute docstring """

    @strawberry.field(description="f1 description")
    def f1(self, arg1: int) -> int:
        """
        f1 resolver docstring
        Args:
          arg1: arg1 docstring
        """
        return arg1

    @strawberry.field(
        description="f2 description",
        description_sources=DescriptionSources.STRAWBERRY_DESCRIPTIONS,
    )
    def f2(self, arg1: int) -> int:
        """
        f2 resolver docstring
        Args:
          arg1: arg1 docstring
        """
        return arg1

    @strawberry.field(
        description="f3 description",
        description_sources=DescriptionSources.TYPE_DOCSTRINGS,
    )
    def f3(self, arg1: int) -> int:
        """
        f3 resolver docstring
        Args:
          arg1: arg1 docstring
        """
        return arg1

    @strawberry.field(
        description="f4 description",
        description_sources=DescriptionSources.RESOLVER_DOCSTRINGS,
    )
    def f4(self, arg1: int) -> int:
        """
        f4 resolver docstring
        Args:
          arg1: arg1 docstring
        """
        return arg1

    @strawberry.field(
        description="f5 description", description_sources=DescriptionSources.NONE
    )
    def f5(self, arg1: int) -> int:
        """
        f5 resolver docstring
        Args:
          arg1: arg1 docstring
        """
        return arg1


@strawberry.type(
    description="B description", description_sources=DescriptionSources.TYPE_DOCSTRINGS
)
class B:
    """
    B docstring

    Attributes:
        a: a docstring
        b: b docstring
        c: c docstring
        d: d docstring
        e: e docstring

        f1: f1 docstring
        f2: f2 docstring
        f3: f3 docstring
        f4: f4 docstring
        f5: f5 docstring
    """

    a: int = strawberry.field(description="a description")
    """ a attribute docstring """
    b: int = strawberry.field(
        description="b description",
        description_sources=DescriptionSources.STRAWBERRY_DESCRIPTIONS,
    )
    """ b attribute docstring """
    c: int = strawberry.field(
        description="c description",
        description_sources=DescriptionSources.TYPE_DOCSTRINGS,
    )
    """ c attribute docstring """
    d: int = strawberry.field(
        description="d description",
        description_sources=DescriptionSources.TYPE_ATTRIBUTE_DOCSTRINGS,
    )
    """ d attribute docstring """
    e: int = strawberry.field(
        description="e description", description_sources=DescriptionSources.NONE
    )
    """ d attribute docstring """

    @strawberry.field(description="f1 description")
    def f1(self, arg1: int) -> int:
        """
        f1 resolver docstring
        Args:
          arg1: arg1 docstring
        """
        return arg1

    @strawberry.field(
        description="f2 description",
        description_sources=DescriptionSources.STRAWBERRY_DESCRIPTIONS,
    )
    def f2(self, arg1: int) -> int:
        """
        f2 resolver docstring
        Args:
          arg1: arg1 docstring
        """
        return arg1

    @strawberry.field(
        description="f3 description",
        description_sources=DescriptionSources.TYPE_DOCSTRINGS,
    )
    def f3(self, arg1: int) -> int:
        """
        f3 resolver docstring
        Args:
          arg1: arg1 docstring
        """
        return arg1

    @strawberry.field(
        description="f4 description",
        description_sources=DescriptionSources.RESOLVER_DOCSTRINGS,
    )
    def f4(self, arg1: int) -> int:
        """
        f4 resolver docstring
        Args:
          arg1: arg1 docstring
        """
        return arg1

    @strawberry.field(
        description="f5 description", description_sources=DescriptionSources.NONE
    )
    def f5(self, arg1: int) -> int:
        """
        f5 resolver docstring
        Args:
          arg1: arg1 docstring
        """
        return arg1


@strawberry.type
class Query:
    a: A
    b: B


def test_override_description_sources():
    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            description_sources=DescriptionSources.STRAWBERRY_DESCRIPTIONS
        ),
    )

    expected = '''
        """A description"""
        type A {
          """a description"""
          a: Int!

          """b description"""
          b: Int!

          """c docstring"""
          c: Int!

          """d attribute docstring"""
          d: Int!
          e: Int!

          """f1 description"""
          f1(arg1: Int!): Int!

          """f2 description"""
          f2(arg1: Int!): Int!

          """f3 docstring"""
          f3(arg1: Int!): Int!

          """f4 resolver docstring"""
          f4(
            """arg1 docstring"""
            arg1: Int!
          ): Int!
          f5(arg1: Int!): Int!
        }

        """B docstring"""
        type B {
          """a docstring"""
          a: Int!

          """b description"""
          b: Int!

          """c docstring"""
          c: Int!

          """d attribute docstring"""
          d: Int!
          e: Int!

          """f1 docstring"""
          f1(arg1: Int!): Int!

          """f2 description"""
          f2(arg1: Int!): Int!

          """f3 docstring"""
          f3(arg1: Int!): Int!

          """f4 resolver docstring"""
          f4(
            """arg1 docstring"""
            arg1: Int!
          ): Int!
          f5(arg1: Int!): Int!
        }

        type Query {
          a: A!
          b: B!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()
