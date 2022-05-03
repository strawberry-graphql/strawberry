from pathlib import Path
from textwrap import dedent

from strawberry.cli.commands.schema_importer import sdl_importer, sdl_transpiler
from strawberry.cli.commands.schema_importer.import_schema import (
    transform_sdl_into_code,
)


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


def test_simple_type_output_correct_code():
    """
    with a field description and case change
    Test for a required Boolean field type
    """
    s = '''
    type Monster {
        """Is the monster scary?"""
        is_scary: Boolean!
    }
    '''
    code_output = sdl_importer.import_sdl(s)
    expected_code = dedent(
        """\
        import strawberry


        @strawberry.type
        class Monster:
            is_scary: bool = strawberry.field(
                description='''Is the monster scary?''',
            )
        """
    )

    assert code_output == expected_code


def test_simple_optional_boolean_outputs_correct_code():
    """
    with a field description and case change
    Test for a required Boolean field type
    """
    s = '''
    type Monster {
        """Is the monster scary?
        We don't know yet
        """
        is_scary_optional: Boolean
    }
    '''
    code_output = sdl_importer.import_sdl(s)
    expected_code = dedent(
        """\
        import typing

        import strawberry


        @strawberry.type
        class Monster:
            is_scary_optional: typing.Optional[bool] = strawberry.field(
                description='''Is the monster scary?
        We don't know yet''',
            )
        """
    )
    assert code_output == expected_code


def test_import_int_field():
    """Test for a required Int field type with multiline description here"""
    s = '''
    type HolyHandGrenade {
        """Some desc"""
        numberThouShaltCount: Int!
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
        import strawberry


        @strawberry.type
        class HolyHandGrenade:
            number_thou_shalt_count: int = strawberry.field(
                description='''Some desc''',
            )
        """
    )

    assert output == what_it_should_be


def test_import_optional_int_field():
    """Test for a required Int field type with multiline description"""
    s = """
    type HolyHandGrenade {
        numberThouShaltCount: Int
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
        import typing

        import strawberry


        @strawberry.type
        class HolyHandGrenade:
            number_thou_shalt_count: typing.Optional[int]
        """
    )

    assert output == what_it_should_be


# String
def test_import_str_fields():
    """Test for String field types both optional and required"""
    s = '''
    type BridgeOfDeath {
        """What is your name?"""
        question: String!
        answer: String
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
        import typing

        import strawberry


        @strawberry.type
        class BridgeOfDeath:
            question: str = strawberry.field(
                description='''What is your name?''',
            )
            answer: typing.Optional[str]
        """
    )

    assert output == what_it_should_be


# Float
def test_import_float_field():
    """Test for a Float type"""
    s = """
    type Swallow {
        speed: Float!
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
        import strawberry


        @strawberry.type
        class Swallow:
            speed: float
        """
    )

    assert output == what_it_should_be


def test_import_optional_float_field():
    """Test for a Float type"""
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
    what_it_should_be = dedent(
        """\
        import typing

        import strawberry


        @strawberry.type
        class Swallow:
            speed: typing.Optional[float] = strawberry.field(
                description='''What is the airbourn speed
        of unladen african swallow?''',
            )
        """
    )

    assert output == what_it_should_be


# ID
def test_import_id_field():
    """Test for a required ID field type"""
    s = """
    type ArgumentClinic {
        id: ID!
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
        import strawberry


        @strawberry.type
        class ArgumentClinic:
            id: strawberry.ID
        """
    )

    assert output == what_it_should_be


def test_import_optional_id_field():
    """Test for a optional ID field type"""
    s = """
    type ArgumentClinic {
        id: ID
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
        import typing

        import strawberry


        @strawberry.type
        class ArgumentClinic:
            id: typing.Optional[strawberry.ID]
    """
    )

    assert output == what_it_should_be


# endregion
# Enum
def test_import_enum_type():
    """Test for an enum type transpilation"""
    s = """
    enum SwallowSpecies {
        AFRICAN
        EUROPEAN
    }
    """
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
        from enum import Enum\n
        import strawberry


        @strawberry.enum
        class SwallowSpecies(Enum):
            AFRICAN = 'african'
            EUROPEAN = 'european'
    """
    )

    assert output == what_it_should_be


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


# region List types
def test_import_opt_list_opt_str_field():
    """Test for an optional list of optional strings type with field description"""
    s = '''
    type HollyHandGrenade {
        """And the people did feast on:"""
        animals: [String]
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
        import typing

        import strawberry


        @strawberry.type
        class HollyHandGrenade:
            animals: typing.Optional[typing.List[typing.Optional[str]]] = strawberry.field(
                description='''And the people did feast on:''',
            )
        """
    )
    assert output == what_it_should_be


def test_import_list_opt_str_field():
    """Test for a required list of optional strings type with field description"""
    s = '''
    type HollyHandGrenade {
        """And the people did feast on:"""
        animals: [String]!
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
       import typing

       import strawberry


       @strawberry.type
       class HollyHandGrenade:
           animals: typing.List[typing.Optional[str]] = strawberry.field(
               description='''And the people did feast on:''',
           )
        """
    )

    assert output == what_it_should_be


def test_import_opt_list_str_field():
    """Test for an optional list of required strings type with field description"""
    s = '''
    type HollyHandGrenade {
        """And the people did feast on:"""
        animals: [String!]
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
       import typing

       import strawberry


       @strawberry.type
       class HollyHandGrenade:
           animals: typing.Optional[typing.List[str]] = strawberry.field(
               description='''And the people did feast on:''',
           )
        """
    )

    assert output == what_it_should_be


def test_import_list_str_field():
    """Test for an required list of required strings type with field description"""
    s = '''
    type HollyHandGrenade {
        """And the people did feast on:"""
        animals: [String!]!
    }
    '''
    output = sdl_importer.import_sdl(s)
    what_it_should_be = dedent(
        """\
       import typing

       import strawberry


       @strawberry.type
       class HollyHandGrenade:
           animals: typing.List[str] = strawberry.field(
               description='''And the people did feast on:''',
           )
    """
    )
    assert output == what_it_should_be


def test_get_field_name():
    """test field name attribute acquisition"""
    assert sdl_transpiler.get_field_name("camelAstName") == ""
    assert sdl_transpiler.get_field_name("snacamel") == ""


def test_click_entrypoint():
    path_to_schema = Path(__file__).parent / "data" / "simple_schema.gql"
    expected_code_path = Path(__file__).parent / "data" / "simple_schema.py"

    code = transform_sdl_into_code(str(path_to_schema))
    assert code == expected_code_path.read_text(), print(code)
