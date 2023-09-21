import ast
import textwrap
from pathlib import Path

from pytest_snapshot.plugin import Snapshot

from strawberry.schema_codegen import codegen

HERE = Path(__file__).parent


def test_long_descriptions(snapshot: Snapshot):
    snapshot.snapshot_dir = HERE / "snapshots"

    schema = '''
    """A connection to a list of items."""
    type FilmCharactersConnection {
    """Information to aid in pagination."""
    pageInfo: PageInfo!

    """A list of edges."""
    edges: [FilmCharactersEdge]

    """
    A count of the total number of objects in this connection, ignoring pagination.
    This allows a client to fetch the first five objects by passing "5" as the
    argument to "first", then fetch the total count so it could display "5 of 83",
    for example.
    """
    totalCount: Int

    """
    A list of all of the objects returned in the connection. This is a convenience
    field provided for quickly exploring the API; rather than querying for
    "{ edges { node } }" when no edge data is needed, this field can be be used
    instead. Note that when clients like Relay need to fetch the "cursor" field on
    the edge to enable efficient pagination, this shortcut cannot be used, and the
    full "{ edges { node } }" version should be used instead.
    """
    characters: [Person]
    }
    '''

    output = codegen(schema)

    ast.parse(output)

    snapshot.assert_match(output, "long_descriptions.py")


def test_can_convert_descriptions_with_quotes():
    schema = '''
    """A type of person or character within the "Star Wars" Universe."""
    type Species {
        """The classification of this species, such as "mammal" or "reptile"."""
        classification: String!
    }
    '''

    output = codegen(schema)

    expected_output = textwrap.dedent(
        """
        import strawberry

        @strawberry.type(description='A type of person or character within the "Star Wars" Universe.')
        class Species:
            classification: str = strawberry.field(description='The classification of this species, such as "mammal" or "reptile".')
        """
    ).lstrip()

    assert output == expected_output
