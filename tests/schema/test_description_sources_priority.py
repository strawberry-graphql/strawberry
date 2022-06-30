import textwrap

import strawberry
from strawberry.description_sources import DescriptionSources
from strawberry.schema.config import StrawberryConfig


@strawberry.type(description="Query description")
class Query:
    """
    Query docstring

    Attributes:
        a: a docstring
        b: b docstring
        c: c docstring
        d: d docstring
    """

    a: int = strawberry.field(description="a description")
    """ a attribute docstring """

    b: int = strawberry.field(description="b description")
    # no attribute docstring

    c: int = strawberry.field()
    """ c attribute docstring """

    d: int = strawberry.field()
    # no attribute docstring

    e: int = strawberry.field(description="e description")
    """ e attribute docstring """

    f: int = strawberry.field(description="f description")
    # no attribute docstring

    g: int = strawberry.field()
    """ g attribute docstring """

    h: int = strawberry.field()
    # no attribute docstring


def test_description():
    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            description_sources=DescriptionSources.STRAWBERRY_DESCRIPTIONS
        ),
    )
    expected = '''
        """Query description"""
        type Query {
          """a description"""
          a: Int!

          """b description"""
          b: Int!
          c: Int!
          d: Int!

          """e description"""
          e: Int!

          """f description"""
          f: Int!
          g: Int!
          h: Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_description_docstring():
    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            description_sources=DescriptionSources.STRAWBERRY_DESCRIPTIONS
            | DescriptionSources.TYPE_DOCSTRINGS
        ),
    )
    expected = '''
        """Query description"""
        type Query {
          """a description"""
          a: Int!

          """b description"""
          b: Int!

          """c docstring"""
          c: Int!

          """d docstring"""
          d: Int!

          """e description"""
          e: Int!

          """f description"""
          f: Int!
          g: Int!
          h: Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_description_typedoc_attrdoc():
    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            description_sources=DescriptionSources.STRAWBERRY_DESCRIPTIONS
            | DescriptionSources.TYPE_ATTRIBUTE_DOCSTRINGS
            | DescriptionSources.TYPE_DOCSTRINGS
        ),
    )
    expected = '''
        """Query description"""
        type Query {
          """a description"""
          a: Int!

          """b description"""
          b: Int!

          """c attribute docstring"""
          c: Int!

          """d docstring"""
          d: Int!

          """e description"""
          e: Int!

          """f description"""
          f: Int!

          """g attribute docstring"""
          g: Int!
          h: Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()
