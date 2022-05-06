from pathlib import Path
from textwrap import dedent

import pytest

from strawberry.cli.commands.schema_importer import sdl_importer
from strawberry.cli.commands.schema_importer.import_schema import (
    import_schema as cmd_import_schema,
    transform_sdl_into_code,
)
from strawberry.cli.commands.schema_importer.sdl_transpiler import get_field_name


def test_get_field_name():
    assert get_field_name("camelCase") == "camelCase"
    assert get_field_name("snake_case") == ""


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
    output = sdl_importer.generate_code_from_sdl(s)
    assert output


# Interface
def test_import_interface_type():
    """Test for an enum type transpilation"""
    s = """
    interface Monster {
        name: String!
    }
    """
    output = sdl_importer.generate_code_from_sdl(s)
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
    output = sdl_importer.generate_code_from_sdl(s)
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

    output = sdl_importer.generate_code_from_sdl(s)

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

    output = sdl_importer.generate_code_from_sdl(s)

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


@pytest.mark.parametrize(
    "file",
    [
        "list_of",
        "simple_schema",
        "data_types",
        "with_enum",
        "custom_type",
        "with_union",
        "directives",
        "different_name",
        "deprecated",
    ],
)
def test_code_generation(file):
    path_to_schema = Path(__file__).parent / "data" / f"{file}.gql"
    expected_code = (Path(__file__).parent / "data" / f"{file}.py").read_text()

    code = transform_sdl_into_code(str(path_to_schema))
    assert code == expected_code, print(code)


def test_file_not_found_error(cli_runner):
    result = cli_runner.invoke(cmd_import_schema, ["abc.sdl"])

    assert result.exit_code == 1
    assert result.output == "File not found on path: abc.sdl\n"


def test_invalid_gql_file_error(cli_runner):
    invalid_schema = Path(__file__).parent / "data" / "invalid.gql"

    result = cli_runner.invoke(cmd_import_schema, [str(invalid_schema)])

    assert result.exit_code == 1
    assert "syntax errors" in result.output


def test_valid_cli_invocation(cli_runner):
    invalid_schema = Path(__file__).parent / "data" / "simple_schema.gql"

    result = cli_runner.invoke(cmd_import_schema, [str(invalid_schema)])
    assert result.exit_code == 0
    assert result.output == dedent(
        """\
        # Code autogenerated by strawberry
        import strawberry


        @strawberry.type
        class Query:
            a_field: str

        """
    )
