from __future__ import annotations

import base64
import dataclasses
import sys
from typing import TYPE_CHECKING, Any, Tuple, Union
from typing_extensions import Self, assert_never

from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.nodes import InlineFragment, Selection

if TYPE_CHECKING:
    from strawberry.types.info import Info


def from_base64(value: str) -> Tuple[str, str]:
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


def to_base64(type_: Union[str, type, StrawberryObjectDefinition], node_id: Any) -> str:
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


def should_resolve_list_connection_edges(info: Info) -> bool:
    """Check if the user requested to resolve the `edges` field of a connection.

    Args:
        info:
            The strawberry execution info resolve the type name from

    Returns:
        True if the user requested to resolve the `edges` field of a connection, False otherwise.

    """
    resolve_for_field_names = {"edges", "pageInfo"}

    def _check_selection(selection: Selection) -> bool:
        """Recursively inspect the selection to check if the user requested to resolve the `edges` field.

        Args:
            selection (Selection): The selection to check.

        Returns:
            bool: True if the user requested to resolve the `edges` field of a connection, False otherwise.
        """
        if (
            not isinstance(selection, InlineFragment)
            and selection.name in resolve_for_field_names
        ):
            return True
        if selection.selections:
            return any(
                _check_selection(selection) for selection in selection.selections
            )
        return False

    for selection_field in info.selected_fields:
        for selection in selection_field.selections:
            if _check_selection(selection):
                return True
    return False


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
        info: Info,
        *,
        before: str | None = None,
        after: str | None = None,
        first: int | None = None,
        last: int | None = None,
    ) -> Self:
        """Get the slice metadata to use on ListConnection."""
        from strawberry.relay.types import PREFIX

        max_results = info.schema.config.relay_max_results
        start = 0
        end: int | None = None

        if after:
            after_type, after_parsed = from_base64(after)
            if after_type != PREFIX:
                raise TypeError("Argument 'after' contains a non-existing value.")

            start = int(after_parsed) + 1
        if before:
            before_type, before_parsed = from_base64(before)
            if before_type != PREFIX:
                raise TypeError("Argument 'before' contains a non-existing value.")
            end = int(before_parsed)

        if isinstance(first, int):
            if first < 0:
                raise ValueError("Argument 'first' must be a non-negative integer.")

            if first > max_results:
                raise ValueError(
                    f"Argument 'first' cannot be higher than {max_results}."
                )

            if end is not None:
                start = max(0, end - 1)

            end = start + first
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

        expected = end - start if end != sys.maxsize else None

        return cls(
            start=start,
            end=end,
            expected=expected,
        )


__all__ = [
    "from_base64",
    "to_base64",
    "should_resolve_list_connection_edges",
    "SliceMetadata",
]
