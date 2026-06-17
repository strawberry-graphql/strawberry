from __future__ import annotations

import dataclasses
import re
from collections.abc import Mapping
from math import isfinite
from typing import TYPE_CHECKING, Any, cast

from graphql.language import (
    BooleanValueNode,
    EnumValueNode,
    FloatValueNode,
    IntValueNode,
    ListValueNode,
    NameNode,
    NullValueNode,
    ObjectFieldNode,
    ObjectValueNode,
    StringValueNode,
)
from graphql.pyutils import Undefined, inspect, is_iterable
from graphql.type import (
    GraphQLID,
    is_enum_type,
    is_input_object_type,
    is_leaf_type,
    is_list_type,
    is_non_null_type,
)

import strawberry
from strawberry.types.base import StrawberryMaybe, has_object_definition

if TYPE_CHECKING:
    from graphql.language import ValueNode
    from graphql.type import (
        GraphQLInputObjectType,
        GraphQLInputType,
        GraphQLList,
        GraphQLNonNull,
    )

    from strawberry.types.field import StrawberryField

__all__ = ["ast_from_value"]

_re_integer_string = re.compile("^-?(?:0|[1-9][0-9]*)$")


def ast_from_leaf_type(serialized: object, type_: GraphQLInputType | None) -> ValueNode:
    # Others serialize based on their corresponding Python scalar types.
    if isinstance(serialized, bool):
        return BooleanValueNode(value=serialized)

    # Python ints and floats correspond nicely to Int and Float values.
    if isinstance(serialized, int):
        return IntValueNode(value=str(serialized))
    if isinstance(serialized, float) and isfinite(serialized):
        value = str(serialized)
        value = value.removesuffix(".0")
        return FloatValueNode(value=value)

    if isinstance(serialized, str):
        # Enum types use Enum literals.
        if type_ and is_enum_type(type_):
            return EnumValueNode(value=serialized)

        # ID types can use Int literals.
        if type_ is GraphQLID and _re_integer_string.match(serialized):
            return IntValueNode(value=serialized)

        return StringValueNode(value=serialized)

    if isinstance(serialized, dict):
        return ObjectValueNode(
            fields=tuple(
                ObjectFieldNode(
                    name=NameNode(value=key),
                    value=ast_from_leaf_type(value, None),
                )
                for key, value in serialized.items()
            )
        )

    raise TypeError(
        f"Cannot convert value to AST: {inspect(serialized)}."
    )  # pragma: no cover


def get_strawberry_field(field: Any) -> StrawberryField | None:
    if not (extensions := field.extensions):
        return None

    return extensions.get("strawberry-definition")


def get_field_python_name(field: Any) -> str | None:
    if (out_name := getattr(field, "out_name", None)) is not None:
        return out_name

    if (strawberry_field := get_strawberry_field(field)) is None:
        return None

    return strawberry_field.python_name


def get_field_value(
    field_name: str,
    field_python_name: str | None,
    value: Mapping[str, Any],
) -> Any:
    if field_name in value:
        return value[field_name]

    if field_python_name is not None and field_python_name in value:
        return value[field_python_name]

    return Undefined


def object_to_shallow_dict(value: Any) -> dict[str, Any]:
    type_definition = (
        value.__strawberry_definition__ if has_object_definition(value) else None
    )
    result = {}

    for field in dataclasses.fields(value):
        field_value = getattr(value, field.name)
        if field_value is strawberry.UNSET:
            continue

        if (
            field_value is None
            and type_definition is not None
            and (strawberry_field := type_definition.get_field(field.name)) is not None
            and isinstance(strawberry_field.type, StrawberryMaybe)
        ):
            continue

        if isinstance(field_value, strawberry.Some):
            field_value = field_value.value

        result[field.name] = field_value

    return result


def should_print_null_field(
    field_python_name: str | None,
    value: Any,
    skip_default_null_fields: bool,
) -> bool:
    if not skip_default_null_fields:
        return True

    if not dataclasses.is_dataclass(value) or isinstance(value, type):
        return False

    if field_python_name is None:
        return False

    type_definition = (
        value.__strawberry_definition__ if has_object_definition(value) else None
    )
    if isinstance(
        field_value := getattr(value, field_python_name, Undefined),
        strawberry.Some,
    ):
        return True

    if field_value is not None:
        return False

    return any(
        getattr(value, field.name) is strawberry.UNSET
        for field in dataclasses.fields(value)
        if type_definition is None or type_definition.get_field(field.name) is not None
    )


def ast_from_value(
    value: Any,
    type_: GraphQLInputType,
    skip_default_null_fields: bool = False,
) -> ValueNode | None:
    # custom ast_from_value that allows to also serialize custom scalar that aren't
    # basic types, namely JSON scalar types

    if is_non_null_type(type_):
        type_ = cast("GraphQLNonNull", type_)
        ast_value = ast_from_value(
            value,
            type_.of_type,
            skip_default_null_fields,
        )
        if isinstance(ast_value, NullValueNode):
            return None
        return ast_value

    # only explicit None, not Undefined or NaN
    if value is None:
        return NullValueNode()

    # undefined
    if value is Undefined:
        return None

    # Convert Python list to GraphQL list. If the GraphQLType is a list, but the value
    # is not a list, convert the value using the list's item type.
    if is_list_type(type_):
        type_ = cast("GraphQLList", type_)
        item_type = type_.of_type
        if is_iterable(value):
            maybe_value_nodes = (
                ast_from_value(item, item_type, skip_default_null_fields)
                for item in value
            )
            value_nodes = tuple(node for node in maybe_value_nodes if node)
            return ListValueNode(values=value_nodes)
        return ast_from_value(value, item_type, skip_default_null_fields)

    # Populate the fields of the input object by creating ASTs from each value in the
    # Python dict according to the fields in the input type.
    if is_input_object_type(type_):
        object_value = value
        if has_object_definition(value):
            value = object_to_shallow_dict(value)
            skip_default_null_fields = True

        if value is None or not isinstance(value, Mapping):
            return None

        type_ = cast("GraphQLInputObjectType", type_)
        field_nodes = []
        for field_name, field in type_.fields.items():
            field_python_name = get_field_python_name(field)
            if (
                field_value := get_field_value(field_name, field_python_name, value)
            ) is Undefined:
                continue

            if field_value is None and not should_print_null_field(
                field_python_name,
                object_value,
                skip_default_null_fields,
            ):
                continue

            if (
                ast_value := ast_from_value(
                    field_value,
                    field.type,
                    skip_default_null_fields,
                )
            ) is not None:
                field_nodes.append(
                    ObjectFieldNode(name=NameNode(value=field_name), value=ast_value)
                )

        return ObjectValueNode(fields=tuple(field_nodes))

    if is_leaf_type(type_):
        # Since value is an internally represented value, it must be serialized to an
        # externally represented value before converting into an AST.
        serialized = type_.serialize(value)  # type: ignore
        if serialized is None or serialized is Undefined:
            return None  # pragma: no cover

        return ast_from_leaf_type(serialized, type_)

    # Not reachable. All possible input types have been considered.
    raise TypeError(f"Unexpected input type: {inspect(type_)}.")  # pragma: no cover


__all__ = ["ast_from_value"]
