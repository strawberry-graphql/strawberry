from pathlib import Path
from textwrap import dedent

import pytest

from strawberry.cli.commands.schema_importer import sdl_importer
from strawberry.cli.commands.schema_importer.import_schema import (
    transform_sdl_into_code,
)


def test_import_specific_object_type(mocker):
    s = '''
    """A single film."""
    type Film implements Node {
    """The title of this film."""
    title: String

    """The episode number of this film."""
    episodeID: Int

    """The opening paragraphs at the beginning of this film."""
    openingCrawl: String

    """The name of the director of this film."""
    director: String

    """The name(s) of the producer(s) of this film."""
    producers: [String]

    """The ISO 8601 date format of film release at original creator country."""
    releaseDate: String
    speciesConnection(after: String, first: Int, before: String, last: Int):
    FilmSpeciesConnection
    starshipConnection(after: String, first: Int, before: String, last: Int):
    FilmStarshipsConnection
    vehicleConnection(after: String, first: Int, before: String, last: Int):
    FilmVehiclesConnection
    characterConnection(after: String, first: Int, before: String, last: Int):
    FilmCharactersConnection
    planetConnection(after: String, first: Int, before: String, last: Int):
    FilmPlanetsConnection

    """The ISO 8601 date format of the time that this resource was created."""
    created: String

    """The ISO 8601 date format of the time that this resource was edited."""
    edited: String

    """The ID of an object"""
    id: ID!
    }
    '''
    output = sdl_importer.import_sdl(s)
    assert output


# Union
def test_import_union_type():
    s = "union Result = Book | Author"
    output = sdl_importer.import_sdl(s)

    what_it_should_be = dedent(
        """\
       import strawberry


       Result = strawberry.union(
           'Result',
           (Book, Author),
       )
       """
    )

    assert output == what_it_should_be


def test_import_union_with_description():
    s = '''
    """
    How do you defend yourself
    against an attacker armed with fruit?
    """
    union Result = Orange | Bannana
    '''

    output = sdl_importer.import_sdl(s)

    what_it_should_be = dedent(
        """\
        import strawberry


        Result = strawberry.union(
            'Result',
            (Orange, Bannana),
            description='''How do you defend yourself
        against an attacker armed with fruit?'''
        )
        """
    )

    assert output == what_it_should_be


# Interface
def test_import_interface_type():
    """Test for an enum type transpilation"""
    s = """
    interface Monster {
        name: String!
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
       import strawberry


       @strawberry.interface
       class Monster:
           name: str
    """
    )

    assert output == what_it_should_be


# Input
def test_import_input_type():
    """Test for input type transpilation"""
    s = """
    input Monster {
        name: String!
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
       import strawberry


       @strawberry.input
       class Monster:
           name: str
    """
    )

    assert output == what_it_should_be


# Directives
def test_directives_description():
    s = '''
    """Make string uppercase"""
    directive @uppercase(example: String!) on FIELD_DEFINITION
    '''

    output = sdl_importer.import_sdl(s)

    what_it_should_be = dedent(
        """\
        from strawberry.directive import DirectiveLocation

        import strawberry


        @strawberry.directive(
            locations=[
                DirectiveLocation.FIELD_DEFINITION
            ],
            description='''Make string uppercase'''
        )
        def uppercase(
            example: str
        ):
            pass
        """
    )

    assert output == what_it_should_be


def test_directives():
    s = """
    directive @uppercase(example: String!) on FIELD_DEFINITION
    """

    output = sdl_importer.import_sdl(s)

    what_it_should_be = dedent(
        """\
       from strawberry.directive import DirectiveLocation

       import strawberry


       @strawberry.directive(
           locations=[
               DirectiveLocation.FIELD_DEFINITION
           ],
       )
       def uppercase(
           example: str
       ):
           pass
    """
    )

    assert output == what_it_should_be


def test_depricated():
    """Test depricated directive both definition and schema directive"""
    s = """
    type ExampleType {
    newField: String
    oldField: String @deprecated(reason: "Use `newField`.")
    }"""

    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
       import typing

       import strawberry


       @strawberry.type
       class ExampleType:
           new_field: typing.Optional[str]
           old_field: typing.Optional[str] = strawberry.field(
               derpecation_reason='Use `newField`.',
           )
        """
    )
    assert output == what_it_should_be


@pytest.mark.parametrize(
    "file", ["list_of", "simple_schema", "data_types", "enums", "custom_type", "union"]
)
def test_list_of(file):
    path_to_schema = Path(__file__).parent / "data" / f"{file}.gql"
    expected_code = (Path(__file__).parent / "data" / f"{file}.py").read_text()

    code = transform_sdl_into_code(str(path_to_schema))
    assert code == expected_code, print(code)
