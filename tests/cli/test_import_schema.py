from strawberry.cli.commands.schema_importer import sdl_importer, sdl_transpiler


# Complex object
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


# region Scalars
# Boolean
def test_import_bool_field():
    """
    Test for a required Boolean field type
    with a field description and case change
    """
    s = '''
    type Woman {
        """
        If a woman weighs less than a duck,
        then she is a...?
        """
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
        "        description='''If a woman weighs less than a duck,\n"
        "then she is a...?''',\n"
        "    )"
    )

    assert output == what_it_should_be


def test_import_optional_bool_field():
    """
    Test for a optional Boolean field type
    with a field description and case change
    """
    s = '''
    type Woman {
        """
        If a woman weighs less than a duck,
        then she is a witch ?
        """
        isWitch: Boolean
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import typing\n\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class Woman:\n"
        "    is_witch: typing.Optional[bool] = strawberry.field(\n"
        "        description='''If a woman weighs less than a duck,\n"
        "then she is a witch ?''',\n"
        "    )"
    )

    assert output == what_it_should_be


# Int
def test_import_int_field():
    """Test for a required Int field type with multiline description here"""
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
        "        description='''First shalt thou take out the Holy Pin.\n"
        "Then shalt thou count to...''',\n"
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
        "import typing\n\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class HolyHandGrenade:\n"
        "    number_thou_shalt_count: typing.Optional[int] = strawberry.field(\n"
        "        description='''First shalt thou take out the Holy Pin.\n"
        "Then shalt thou count to...''',\n"
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
        "import typing\n\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type(description='''He who wants to cross the bridge,\n"
        "must answer me these questions three,\n"
        "and the other side he see...''')\n"
        "class BridgeOfDeath:\n"
        "    question: str = strawberry.field(\n"
        "        description='''What is your name?''',\n"
        "    )\n"
        "    answer: typing.Optional[str]"
    )

    assert output == what_it_should_be


# Float
def test_import_float_field():
    """ Test for a Float type """
    s = '''
    type Swallow {
        """
        What is the airbourn speed
        of unladen african swallow?
        """
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
        "        description='''What is the airbourn speed\n"
        "of unladen african swallow?''',\n"
        "    )"
    )

    assert output == what_it_should_be


def test_import_optional_float_field():
    """ Test for a Float type """
    s = '''
    type Swallow {
        """
        What is the airbourn speed
        of unladen african swallow?
        """
        speed: Float
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import typing\n\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class Swallow:\n"
        "    speed: typing.Optional[float] = strawberry.field(\n"
        "        description='''What is the airbourn speed\n"
        "of unladen african swallow?''',\n"
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


def test_import_optional_id_field():
    """ Test for a optional ID field type """
    s = """
    type ArgumentClinic {
        id: ID
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import typing\n\n"
        "import strawberry\n"
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
        "from enum import Enum\n\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.enum\n"
        "class SwallowSpecies(Enum):\n"
        "    AFRICAN = 'african'\n"
        "    EUROPEAN = 'european'"
    )

    assert output == what_it_should_be


# Union
def test_import_union_type():
    s = "union Result = Book | Author"
    output = sdl_importer.import_sdl(s)

    what_it_should_be = (
        "import strawberry\n"
        "\n"
        "\n"
        "Result = strawberry.union(\n"
        "    'Result',\n"
        "    (Book, Author),\n"
        ")"
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

    what_it_should_be = (
        "import strawberry\n"
        "\n"
        "\n"
        "Result = strawberry.union(\n"
        "    'Result',\n"
        "    (Orange, Bannana),\n"
        "    description='''How do you defend yourself\n"
        "against an attacker armed with fruit?'''\n"
        ")"
    )

    assert output == what_it_should_be


# Interface
def test_import_interface_type():
    """ Test for an enum type transpilation """
    s = """
    interface Monster {
        name: String!
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.interface\n"
        "class Monster:\n"
        "    name: str"
    )

    assert output == what_it_should_be


# Input
def test_import_input_type():
    """ Test for input type transpilation """
    s = """
    input Monster {
        name: String!
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.input\n"
        "class Monster:\n"
        "    name: str"
    )

    assert output == what_it_should_be


# Directives
def test_directives_description():
    s = '''
    """Make string uppercase"""
    directive @uppercase(example: String!) on FIELD_DEFINITION
    '''

    output = sdl_importer.import_sdl(s)

    what_it_should_be = (
        "from strawberry.directive import DirectiveLocation\n"
        "\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.directive(\n"
        "    locations=[\n"
        "        DirectiveLocation.FIELD_DEFINITION\n"
        "    ],\n"
        "    description='''Make string uppercase'''\n"
        ")\n"
        "def uppercase(\n"
        "    example: str\n"
        "):\n"
        "    pass"
    )

    assert output == what_it_should_be


def test_directives():
    s = """
    directive @uppercase(example: String!) on FIELD_DEFINITION
    """

    output = sdl_importer.import_sdl(s)

    what_it_should_be = (
        "from strawberry.directive import DirectiveLocation\n"
        "\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.directive(\n"
        "    locations=[\n"
        "        DirectiveLocation.FIELD_DEFINITION\n"
        "    ],\n"
        ")\n"
        "def uppercase(\n"
        "    example: str\n"
        "):\n"
        "    pass"
    )

    assert output == what_it_should_be


def test_depricated():
    """ Test depricated directive both definition and schema directive """
    s = """
    type ExampleType {
    newField: String
    oldField: String @deprecated(reason: "Use `newField`.")
    }"""

    output = sdl_importer.import_sdl(s)
    what_it_should_be = (
        "import typing\n"
        "\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class ExampleType:\n"
        "    new_field: typing.Optional[str]\n"
        "    old_field: typing.Optional[str] = strawberry.field(\n"
        "        derpecation_reason='Use `newField`.',\n"
        "    )"
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
    field = "= strawberry.field(\n"
    string = "    animals: typing.Optional[typing.List[typing.Optional[str]]] "
    stringField = string + field
    what_it_should_be = (
        f"import typing\n\n"
        f"import strawberry\n"
        f"\n"
        f"\n"
        f"@strawberry.type\n"
        f"class HollyHandGrenade:\n"
        f"{stringField}"
        f"        description='''And the people did feast on:''',\n"
        f"    )"
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
        "import typing\n\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class HollyHandGrenade:\n"
        "    animals: typing.List[typing.Optional[str]] = strawberry.field(\n"
        "        description='''And the people did feast on:''',\n"
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
        "import typing\n\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class HollyHandGrenade:\n"
        "    animals: typing.Optional[typing.List[str]] = strawberry.field(\n"
        "        description='''And the people did feast on:''',\n"
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
        "import typing\n\n"
        "import strawberry\n"
        "\n"
        "\n"
        "@strawberry.type\n"
        "class HollyHandGrenade:\n"
        "    animals: typing.List[str] = strawberry.field(\n"
        "        description='''And the people did feast on:''',\n"
        "    )"
    )

    assert output == what_it_should_be


# endregion

# region
def test_get_field_name():
    """ test field name attribute acquisition """
    assert sdl_transpiler.get_field_name("non_camel_ast_name") == "non_camel_ast_name"
    assert sdl_transpiler.get_field_name("camelAstName") == ""
    assert sdl_transpiler.get_field_name("snacamel") == ""
