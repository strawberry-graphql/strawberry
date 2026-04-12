import pytest
from graphql.error import GraphQLError

from strawberry.utils.schema_diff import (
    build_schema_from_sdl,
    find_breaking_changes_between_sdls,
)


def test_find_breaking_changes_between_sdls_identical() -> None:
    sdl = """
    type Query {
        hello: String
    }
    """
    assert find_breaking_changes_between_sdls(sdl, sdl) == []


def test_find_breaking_changes_between_sdls_field_removed() -> None:
    old = """
    type Query {
        hello: String
        world: String
    }
    """
    new = """
    type Query {
        hello: String
    }
    """
    changes = find_breaking_changes_between_sdls(old, new)
    descriptions = [change.description for change in changes]
    assert any("world" in description for description in descriptions)


def test_build_schema_from_sdl_invalid_raises() -> None:
    with pytest.raises(GraphQLError):
        build_schema_from_sdl("{ not valid")


def test_find_breaking_changes_invalid_old_sdl_raises() -> None:
    with pytest.raises(GraphQLError):
        find_breaking_changes_between_sdls(
            "{ not valid", "type Query { hello: String }"
        )


def test_find_breaking_changes_invalid_new_sdl_raises() -> None:
    with pytest.raises(GraphQLError):
        find_breaking_changes_between_sdls(
            "type Query { hello: String }", "{ not valid"
        )