import os

from click.testing import CliRunner

from strawberry.cli.commands.schema_importer import (
    import_schema,
    sdl_importer,
    ast_converter,
    sdl_transpiler,
)


def test_cli_import_whole_schema(mocker):

    runner = CliRunner()
    file = os.path.join(os.getcwd(), "utils", "helpers", "swapi_schema.gql")
    result = runner.invoke(import_schema.import_schema, [file], "-R")
    assert result.exit_code == 0


def test_cli_cmd_import_specific_object_type(mocker):
    runner = CliRunner()
    string_type = '''
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
    speciesConnection(after: String, first: Int, before: String, last: Int): FilmSpeciesConnection
    starshipConnection(after: String, first: Int, before: String, last: Int): FilmStarshipsConnection
    vehicleConnection(after: String, first: Int, before: String, last: Int): FilmVehiclesConnection
    characterConnection(after: String, first: Int, before: String, last: Int): FilmCharactersConnection
    planetConnection(after: String, first: Int, before: String, last: Int): FilmPlanetsConnection

    """The ISO 8601 date format of the time that this resource was created."""
    created: String

    """The ISO 8601 date format of the time that this resource was edited."""
    edited: String

    """The ID of an object"""
    id: ID!
    }
    '''
    result = runner.invoke(import_schema.import_schema, [string_type])
    # Just so it's easier to read the result it is in the .gitignore file
    assert result.exit_code == 0
