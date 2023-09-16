import textwrap

from strawberry.schema_codegen import codegen


def test_enum():
    schema = """
    enum AuthStateNameEnum {
        AUTH_BROWSER_LAUNCHED
        AUTH_COULD_NOT_LAUNCH_BROWSER
        AUTH_ERROR_DURING_LOGIN
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from enum import Enum

        @strawberry.enum
        class AuthStateNameEnum(Enum):
            AUTH_BROWSER_LAUNCHED = "AUTH_BROWSER_LAUNCHED"
            AUTH_COULD_NOT_LAUNCH_BROWSER = "AUTH_COULD_NOT_LAUNCH_BROWSER"
            AUTH_ERROR_DURING_LOGIN = "AUTH_ERROR_DURING_LOGIN"
        """
    ).strip()

    assert codegen(schema).strip() == expected


# TODO: descriptions
def test_multiple_enums_single_import():
    schema = """
    enum AuthStateNameEnum {
        AUTH_BROWSER_LAUNCHED
    }

    enum AuthStateNameEnum2 {
        AUTH_COULD_NOT_LAUNCH_BROWSER
    }
    """

    expected = textwrap.dedent(
        """
        import strawberry
        from enum import Enum

        @strawberry.enum
        class AuthStateNameEnum(Enum):
            AUTH_BROWSER_LAUNCHED = "AUTH_BROWSER_LAUNCHED"

        @strawberry.enum
        class AuthStateNameEnum2(Enum):
            AUTH_COULD_NOT_LAUNCH_BROWSER = "AUTH_COULD_NOT_LAUNCH_BROWSER"
        """
    ).strip()

    assert codegen(schema).strip() == expected
