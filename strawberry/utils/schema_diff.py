from __future__ import annotations

from typing import TYPE_CHECKING

from graphql import build_schema
from graphql.utilities import find_breaking_changes

if TYPE_CHECKING:
    from graphql.type.schema import GraphQLSchema
    from graphql.utilities.find_breaking_changes import BreakingChange


def build_schema_from_sdl(sdl: str) -> GraphQLSchema:
    """Parse GraphQL SDL into a schema object."""
    return build_schema(sdl)


def find_breaking_changes_between_sdls(
    old_sdl: str, new_sdl: str
) -> list[BreakingChange]:
    """Return breaking changes when moving from ``old_sdl`` to ``new_sdl``.

    ``old_sdl`` is the baseline schema (for example what is in production).
    ``new_sdl`` is the candidate schema you plan to deploy. The returned list
    describes changes that can break clients that were written against the
    baseline schema.
    """
    old_schema = build_schema_from_sdl(old_sdl)
    new_schema = build_schema_from_sdl(new_sdl)
    return find_breaking_changes(old_schema, new_schema)
