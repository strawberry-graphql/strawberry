import base64
from typing import Any, Tuple, Union
from typing_extensions import assert_never

from strawberry.types.info import Info
from strawberry.types.nodes import InlineFragment, Selection
from strawberry.types.types import StrawberryObjectDefinition


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
