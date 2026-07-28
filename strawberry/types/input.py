from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Iterable, Iterator
from functools import partial
from typing import TypeAlias

from strawberry.types.base import (
    StrawberryContainer,
    StrawberryObjectDefinition,
    StrawberryType,
    get_object_definition,
)
from strawberry.types.maybe import Some
from strawberry.utils.await_maybe import await_maybe

CleanOperation: TypeAlias = Callable[[], object]
MaybeAwaitable: TypeAlias = Awaitable[None] | None


def type_has_input_clean_method(type_: StrawberryType | type) -> bool:
    """Return whether an input type graph contains a `clean` method.

    This runs while creating a schema so regular resolvers do not pay for input
    traversal when none of their declared input types supports lifecycle hooks.
    """
    return _type_has_input_clean_method(type_, set())


def _type_has_input_clean_method(
    type_: StrawberryType | type,
    visited: set[StrawberryObjectDefinition],
) -> bool:
    if isinstance(type_, StrawberryContainer):
        return _type_has_input_clean_method(type_.of_type, visited)

    definition = get_object_definition(type_)
    if definition is None or not definition.is_input or definition in visited:
        return False

    visited.add(definition)

    if callable(getattr(definition.origin, "clean", None)):
        return True

    return any(
        _type_has_input_clean_method(field.type, visited) for field in definition.fields
    )


def run_input_clean_methods(values: Iterable[object], info: object) -> MaybeAwaitable:
    """Run clean methods on coerced input objects.

    Nested inputs are visited before their containing input. Synchronous methods run
    immediately; an awaitable is returned only when a method returns an awaitable.
    """
    return _run_clean_operations(partial(_visit_input, value, info) for value in values)


def _run_clean_operations(operations: Iterable[CleanOperation]) -> MaybeAwaitable:
    """Run clean operations until one requires asynchronous continuation."""
    iterator = iter(operations)

    for operation in iterator:
        result = operation()
        if inspect.isawaitable(result):
            return _await_remaining(result, iterator)

    return None


async def _await_remaining(
    pending: Awaitable[object], remaining: Iterator[CleanOperation]
) -> None:
    """Await clean operations sequentially to preserve child-before-parent order."""
    await pending
    for operation in remaining:
        await await_maybe(operation())


def _visit_input(value: object, info: object) -> MaybeAwaitable:
    """Traverse an input value and run its nested lifecycle hooks."""
    if isinstance(value, Some):
        return _visit_input(value.value, info)

    if isinstance(value, (list, tuple)):
        return _run_clean_operations(
            partial(_visit_input, item, info) for item in value
        )

    definition = get_object_definition(value)
    if definition is None or not definition.is_input:
        return None

    return _run_clean_operations(_iter_clean_operations(value, definition, info))


def _iter_clean_operations(
    value: object,
    definition: StrawberryObjectDefinition,
    info: object,
) -> Iterator[CleanOperation]:
    """Yield nested-input visits followed by this input's clean hook."""
    for field in definition.fields:
        assert field.python_name is not None
        field_value = getattr(value, field.python_name)
        yield partial(_visit_input, field_value, info)

    clean = getattr(value, "clean", None)
    if callable(clean):
        yield partial(clean, info)
