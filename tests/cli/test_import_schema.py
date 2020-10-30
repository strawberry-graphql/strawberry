import os

from strawberry.cli.commands.schema_importer import (
    import_schema,
    sdl_importer,
    ast_converter,
    sdl_transpiler,
)

# Complex object
def test_cli_cmd_import_specific_object_type(mocker):
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
    output = sdl_importer.import_sdl(s)
    assert output


# region Scalars
# Boolean
def test_import_bool_field():
    """ Test for a required Boolean field type with a field description and case change """
    s = '''
    type Woman {
        """If a woman weighs less than a duck then she is a...?"""
        isWitch: Boolean!
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class Woman:\n"
        "    is_witch: bool = strawberry.field(\n"
        "        name='isWitch',\n"
        "        description='''If a woman weighs less than a duck then she is a...?'''\n"
        "    )"
    )

    assert output == what_it_should_be


def test_import_optional_bool_field():
    """ Test for a optional Boolean field type with a field description and case change """
    s = '''
    type Woman {
        """If a woman weighs less than a duck then she is a...?"""
        isWitch: Boolean
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "import typing\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class Woman:\n"
        "    is_witch: typing.Optional[bool] = strawberry.field(\n"
        "        name='isWitch',\n"
        "        description='''If a woman weighs less than a duck then she is a...?'''\n"
        "    )"
    )

    assert output == what_it_should_be


# Int
def test_import_int_field():
    """ Test for a required Int field type with multiline description """
    s = '''
    type HolyHandGrenade {
        """
        First shalt thou take out the Holy Pin.
        Then shalt thou count to...
        """
        numberThouShaltCount: Int!
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class HolyHandGrenade:\n"
        "    number_thou_shalt_count: int = strawberry.field(\n"
        "        name='numberThouShaltCount',\n"
        "        description='''First shalt thou take out the Holy Pin.\n"
        "Then shalt thou count to...'''\n"
        "    )"
    )

    assert output == what_it_should_be


def test_import_optional_int_field():
    """ Test for a required Int field type with multiline description """
    s = '''
    type HolyHandGrenade {
        """
        First shalt thou take out the Holy Pin.
        Then shalt thou count to...
        """
        numberThouShaltCount: Int
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "import typing\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class HolyHandGrenade:\n"
        "    number_thou_shalt_count: typing.Optional[int] = strawberry.field(\n"
        "        name='numberThouShaltCount',\n"
        "        description='''First shalt thou take out the Holy Pin.\n"
        "Then shalt thou count to...'''\n"
        "    )"
    )

    assert output == what_it_should_be


# String
def test_import_str_fields():
    """ Test for String field types both optional and required """
    s = '''
    """
    He who wants to cross the bridge,
    must answer me these questions three,
    and the other side he see...
    """
    type BridgeOfDeath {
        """What is your name?"""
        question: String!
        answer: String
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "import typing\n"
        "\n"
        "\n"
        "@strawberry.type(description='''He who wants to cross the bridge,\n"
        "must answer me these questions three,\n"
        "and the other side he see...''')\n"
        "class BridgeOfDeath:\n"
        "    question: str = strawberry.field(\n"
        "        description='''What is your name?'''\n"
        "    )\n"
        "    answer: typing.Optional[str]"
    )

    assert output == what_it_should_be


# Float
def test_import_float_field():
    """ Test for a Float type """
    s = '''
    type Swallow {
        """What is the airbourn speed of unladen african swallow?"""
        speed: Float!
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class Swallow:\n"
        "    speed: float = strawberry.field(\n"
        "        description='''What is the airbourn speed of unladen african swallow?'''\n"
        "    )"
    )

    assert output == what_it_should_be


def test_import_optional_float_field():
    """ Test for a Float type """
    s = '''
    type Swallow {
        """What is the airbourn speed of unladen african swallow?"""
        speed: Float
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "import typing\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class Swallow:\n"
        "    speed: typing.Optional[float] = strawberry.field(\n"
        "        description='''What is the airbourn speed of unladen african swallow?'''\n"
        "    )"
    )

    assert output == what_it_should_be


# ID
def test_import_id_field():
    """ Test for a required ID field type """
    s = """
    type ArgumentClinic {
        id: ID!
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class ArgumentClinic:\n"
        "    id: strawberry.ID"
    )

    assert output == what_it_should_be


def test_import_id_field():
    """ Test for a optional ID field type """
    s = """
    type ArgumentClinic {
        id: ID
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "import typing\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class ArgumentClinic:\n"
        "    id: typing.Optional[strawberry.ID]"
    )

    assert output == what_it_should_be


# endregion
# Enum
def test_import_enum_type():
    """ Test for an enum type transpilation """
    s = """
    enum SwallowSpecies {
        AFRICAN
        EUROPEAN
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.enum\n"
        "class SwallowSpecies:\n"
        "    AFRICAN = 'african'\n"
        "    EUROPEAN = 'european'"
    )

    assert output == what_it_should_be


# region List types
def test_import_opt_list_opt_str_field():
    """ Test for an optional list of optional strings type with field description """
    s = '''
    type HollyHandGrenade {
        """And the people did feast on:"""
        animals: [String]
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "import typing\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class HollyHandGrenade:\n"
        "    animals: typing.Optional[typing.List[typing.Optional[str]]] = strawberry.field(\n"
        "        description='''And the people did feast on:'''\n"
        "    )"
    )

    assert output == what_it_should_be


def test_import_list_opt_str_field():
    """ Test for a required list of optional strings type with field description """
    s = '''
    type HollyHandGrenade {
        """And the people did feast on:"""
        animals: [String]!
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "import typing\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class HollyHandGrenade:\n"
        "    animals: typing.List[typing.Optional[str]] = strawberry.field(\n"
        "        description='''And the people did feast on:'''\n"
        "    )"
    )

    assert output == what_it_should_be


def test_import_opt_list_str_field():
    """ Test for an optional list of required strings type with field description """
    s = '''
    type HollyHandGrenade {
        """And the people did feast on:"""
        animals: [String!]
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "import typing\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class HollyHandGrenade:\n"
        "    animals: typing.Optional[typing.List[str]] = strawberry.field(\n"
        "        description='''And the people did feast on:'''\n"
        "    )"
    )

    assert output == what_it_should_be


def test_import_list_str_field():
    """ Test for an required list of required strings type with field description """
    s = '''
    type HollyHandGrenade {
        """And the people did feast on:"""
        animals: [String!]!
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "import typing\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class HollyHandGrenade:\n"
        "    animals: typing.List[str] = strawberry.field(\n"
        "        description='''And the people did feast on:'''\n"
        "    )"
    )

    assert output == what_it_should_be


# endregion