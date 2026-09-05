import keyword
import textwrap

import pytest

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
        from __future__ import annotations
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


@pytest.mark.parametrize("name", keyword.kwlist)
def test_handles_keyword_enum_values(name: str):
    schema = f"""
    enum Example {{
        {name}
    }}
    """

    expected = textwrap.dedent(
        f"""
        from __future__ import annotations
        import strawberry
        from enum import Enum

        @strawberry.enum
        class Example(Enum):
            {name}_ = strawberry.enum_value("{name}", name="{name}")
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_mixed_keyword_and_non_keyword_enum_values():
    # Only keyword values are aliased; non-keyword values are left as-is and the
    # original ordering is preserved.
    schema = """
    enum Example {
        RED
        class
        BLUE
        import
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from enum import Enum

        @strawberry.enum
        class Example(Enum):
            RED = "RED"
            class_ = strawberry.enum_value("class", name="class")
            BLUE = "BLUE"
            import_ = strawberry.enum_value("import", name="import")
        """
    ).strip()

    assert codegen(schema).strip() == expected


def test_keyword_enum_value_alias_does_not_collide():
    # An enum can contain both a keyword value and its underscore-suffixed
    # counterpart; the generated aliases must stay unique so the generated
    # Enum can be imported.
    schema = """
    enum Example {
        class
        class_
    }
    """

    expected = textwrap.dedent(
        """
        from __future__ import annotations
        import strawberry
        from enum import Enum

        @strawberry.enum
        class Example(Enum):
            class_ = strawberry.enum_value("class", name="class")
            class__ = strawberry.enum_value("class_", name="class_")
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
        from __future__ import annotations
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
