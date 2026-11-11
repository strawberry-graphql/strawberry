from __future__ import annotations

import base64
import dataclasses
import sys
from typing import TYPE_CHECKING, Any, Self, assert_never

from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.nodes import InlineFragment

if TYPE_CHECKING:
    import strawberry


def from_base64(value: str) -> tuple[str, str]:
    """Parse the base64 encoded relay value.

    Args:
        value:
            The value to be parsed

    Returns:
        A tuple of (TypeName, NodeID).

    Raises:
        ValueError:
            If the value is not in the expected format

    """
    try:
        res = base64.b64decode(value.encode()).decode().split(":", 1)
    except Exception as e:
        raise ValueError(str(e)) from e

    if len(res) != 2:
        raise ValueError(f"{res} expected to contain only 2 items")

    return res[0], res[1]


def to_base64(type_: str | type | StrawberryObjectDefinition, node_id: Any) -> str:
    """Encode the type name and node id to a base64 string.

    Args:
        type_:
            The GraphQL type, type definition or type name.
        node_id:
            The node id itself

    Returns:
        A GlobalID, which is a string resulting from base64 encoding <TypeName>:<NodeID>.

    Raises:
        ValueError:
            If the value is not a valid GraphQL type or name

    """
    try:
        if isinstance(type_, str):
            type_name = type_
        elif isinstance(type_, StrawberryObjectDefinition):
            type_name = type_.name
        elif isinstance(type_, type):
            type_name = type_.__strawberry_definition__.name  # type:ignore
        else:  # pragma: no cover
            assert_never(type_)
    except Exception as e:
        raise ValueError(f"{type_} is not a valid GraphQL type or name") from e

    return base64.b64encode(f"{type_name}:{node_id}".encode()).decode()


def should_resolve_list_connection_edges(info: strawberry.Info) -> bool:
    """Check if the user requested to resolve the `edges` field of a connection.

    Args:
        info:
            The strawberry execution info resolve the type name from

    Returns:
        True if the user requested to resolve the `edges` field of a connection, False otherwise.

    """
    resolve_for_field_names = {"edges", "pageInfo"}
    # Recursively inspect the selection to check if the user requested to resolve the `edges` field.
    stack = []
    for selection_field in info.selected_fields:
        stack.extend(selection_field.selections)
    while stack:
        selection = stack.pop()
        if (
            not isinstance(selection, InlineFragment)
            and selection.name in resolve_for_field_names
        ):
            return True
        if nested_selections := getattr(selection, "selections", None):
            stack.extend(nested_selections)
    return False


def _parse_cursor_offset(cursor: str, *, prefix: str, argument: str) -> int:
    """Parse the offset from a `ListConnection` cursor.

    Raises:
        TypeError:
            If the cursor is malformed, has a different prefix or doesn't
            point to a non-negative offset.

    """
    try:
        cursor_type, offset = from_base64(cursor)
    except ValueError:
        cursor_type, offset = None, ""

    # Only accept the plain digits produced by `to_base64`, so that negative
    # offsets can't turn into Python's negative indexing when slicing
    if cursor_type != prefix or not (offset.isascii() and offset.isdigit()):
        raise TypeError(f"Argument '{argument}' contains a non-existing value.")

    return int(offset)


@dataclasses.dataclass
class SliceMetadata:
    start: int
    end: int
    expected: int | None

    @property
    def overfetch(self) -> int:
        # Overfetch by 1 to check if we have a next result
        return self.end + 1 if self.end != sys.maxsize else self.end

    @classmethod
    def from_arguments(
        cls,
        info: strawberry.Info,
        *,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
        max_results: int | None = None,
        prefix: str | None = None,
    ) -> Self:
        """Get the slice metadata to use on ListConnection."""
        from strawberry.relay.types import PREFIX

        if prefix is None:
            prefix = PREFIX

        max_results = (
            max_results
            if max_results is not None
            else info.schema.config.relay_max_results
        )
        start = 0
        end: int | None = None

        if after:
            start = _parse_cursor_offset(after, prefix=prefix, argument="after") + 1
        if before:
            end = _parse_cursor_offset(before, prefix=prefix, argument="before")

        if isinstance(first, int):
            if first < 0:
                raise ValueError("Argument 'first' must be a non-negative integer.")

            if first > max_results:
                raise ValueError(
                    f"Argument 'first' cannot be higher than {max_results}."
                )

            end = min(end, start + first) if end is not None else start + first
        if isinstance(last, int):
            if last < 0:
                raise ValueError("Argument 'last' must be a non-negative integer.")

            if last > max_results:
                raise ValueError(
                    f"Argument 'last' cannot be higher than {max_results}."
                )

            if end is not None:
                start = max(start, end - last)
            else:
                end = sys.maxsize

        if end is None:
            end = start + max_results
        elif end != sys.maxsize:
            # `first` and `last` are already limited to `max_results`, but
            # `before` on its own isn't, so cap it as if `first` was missing
            end = min(end, start + max_results)

        expected = end - start if end != sys.maxsize else None

        return cls(
            start=start,
            end=end,
            expected=expected,
        )


__all__ = [
    "SliceMetadata",
    "from_base64",
    "should_resolve_list_connection_edges",
    "to_base64",
]
