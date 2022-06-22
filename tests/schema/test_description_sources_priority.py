import textwrap

import strawberry
from strawberry.description_source import DescriptionSource
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
            description_sources=[DescriptionSource.STRAWBERRY_DESCRIPTIONS]
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
            description_sources=[
                DescriptionSource.STRAWBERRY_DESCRIPTIONS,
                DescriptionSource.TYPE_DOCSTRINGS,
            ]
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
            description_sources=[
                DescriptionSource.STRAWBERRY_DESCRIPTIONS,
                DescriptionSource.TYPE_DOCSTRINGS,
                DescriptionSource.TYPE_ATTRIBUTE_DOCSTRING,
            ]
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

          """g attribute docstring"""
          g: Int!
          h: Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()


def test_description_attrdoc_typedoc():
    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            description_sources=[
                DescriptionSource.STRAWBERRY_DESCRIPTIONS,
                DescriptionSource.TYPE_ATTRIBUTE_DOCSTRING,
                DescriptionSource.TYPE_DOCSTRINGS,
            ]
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


def test_attrdoc_typedoc_description():
    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            description_sources=[
                DescriptionSource.TYPE_ATTRIBUTE_DOCSTRING,
                DescriptionSource.TYPE_DOCSTRINGS,
                DescriptionSource.STRAWBERRY_DESCRIPTIONS,
            ]
        ),
    )
    expected = '''
        """Query docstring"""
        type Query {
          """a attribute docstring"""
          a: Int!

          """b docstring"""
          b: Int!

          """c attribute docstring"""
          c: Int!

          """d docstring"""
          d: Int!

          """e attribute docstring"""
          e: Int!

          """f description"""
          f: Int!

          """g attribute docstring"""
          g: Int!
          h: Int!
        }
    '''
    assert str(schema) == textwrap.dedent(expected).strip()
