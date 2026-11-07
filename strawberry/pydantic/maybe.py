"""How pydantic validates and serializes `strawberry.Maybe` fields."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_args

from pydantic_core import core_schema

from strawberry.types.maybe import Some

if TYPE_CHECKING:
    from collections.abc import Callable

    from pydantic import GetCoreSchemaHandler
    from pydantic_core import CoreSchema


def _validate(value: Any, validator: Callable[[Any], Any]) -> Some[Any]:
    # the value of a `Some` is validated like a bare one, so a value sent by a
    # client and one given in Python are checked the same way
    if isinstance(value, Some):
        value = value.value

    return Some(validator(value))


def _serialize(value: Any, serializer: Callable[[Any], Any]) -> Any:
    # `None` is a field the client left out
    if value is None:
        return None

    return serializer(value.value if isinstance(value, Some) else value)


def get_maybe_core_schema(source: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
    """Return the core schema of `source`, a `Maybe[T]`.

    A value is validated as `T` and wrapped in `Some`, so a key in the data is a
    field the client sent, with `None` for an explicit null. The field defaults
    to `None` without validating it, so it can be left out, like a `Maybe` field
    of a `@strawberry.input`, and it isn't in `model_fields_set` then.

    `model_dump()` gives the value inside the `Some`, and `None` for a field that
    was left out, so `model_dump(exclude_unset=True)` has the values the client
    sent. The JSON schema is the one of `T`, with a `null` default.
    """
    args = get_args(source)
    inner_schema = handler.generate_schema(args[0] if args else Any)

    schema = core_schema.no_info_wrap_validator_function(
        _validate,
        inner_schema,
        serialization=core_schema.wrap_serializer_function_ser_schema(
            _serialize, schema=inner_schema
        ),
    )

    return core_schema.with_default_schema(schema, default=None, validate_default=False)


__all__ = ["get_maybe_core_schema"]
