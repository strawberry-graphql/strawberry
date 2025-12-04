from __future__ import annotations

import functools
import warnings
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING, Any, get_type_hints

from strawberry.utils.await_maybe import AsyncIteratorOrIterator, AwaitableOrValue

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from strawberry.types import ExecutionContext
    from strawberry.types.info import Info


def _create_info_from_raw(raw_info: GraphQLResolveInfo) -> Info:
    """Create a strawberry Info from raw GraphQLResolveInfo."""
    # Get the strawberry schema from the GraphQL schema
    schema = raw_info.schema._strawberry_schema  # type: ignore

    # Get the strawberry field definition (may not exist for introspection fields)
    strawberry_field = None
    if raw_info.field_name in raw_info.parent_type.fields:
        field_def = raw_info.parent_type.fields[raw_info.field_name]
        strawberry_field = field_def.extensions.get("strawberry-definition")

    # Create Info using the schema's configured info class
    return schema.config.info_class(_raw_info=raw_info, _field=strawberry_field)


def _check_uses_old_resolve_signature(cls: type, base_resolve: Callable) -> bool:
    """Check if a class's resolve method uses the old GraphQLResolveInfo signature."""
    # Check if this class directly defines resolve in its own __dict__
    if "resolve" not in cls.__dict__:
        return False

    resolve_method = cls.__dict__["resolve"]

    # If it's already wrapped, don't wrap again
    if getattr(resolve_method, "_strawberry_wrapped_for_deprecation", False):
        return False

    # First check the raw annotations (handles TYPE_CHECKING imports)
    annotations = getattr(resolve_method, "__annotations__", {})
    info_annotation = annotations.get("info")
    if info_annotation is not None:
        # Convert to string to handle both string annotations and type objects
        annotation_str = (
            info_annotation
            if isinstance(info_annotation, str)
            else getattr(info_annotation, "__name__", str(info_annotation))
        )
        # If it's Info (not GraphQLResolveInfo), it's the new signature
        if "Info" in annotation_str and "GraphQLResolveInfo" not in annotation_str:
            return False
        # If it explicitly uses GraphQLResolveInfo, it's the old signature
        if "GraphQLResolveInfo" in annotation_str:
            return True

    # Fall back to get_type_hints for resolved types
    try:
        hints = get_type_hints(resolve_method)
    except Exception:  # noqa: BLE001
        # If we can't get type hints and no annotation was found, assume new signature
        # (benefit of the doubt - most new code uses Info)
        return False

    info_hint = hints.get("info")
    if info_hint is None:
        # No type hint, assume new signature
        return False

    # Check if the hint is GraphQLResolveInfo (not Info)
    hint_name = getattr(info_hint, "__name__", str(info_hint))
    return "GraphQLResolveInfo" in hint_name


def _wrap_resolve_with_info(
    original_resolve: Callable,
) -> Callable:
    """Wrap a resolve method to convert raw GraphQLResolveInfo to Info."""

    @functools.wraps(original_resolve)
    def wrapped_resolve(
        self: SchemaExtension,
        _next: Callable,
        root: Any,
        info: Info,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        # If info is already an Info object, use it directly
        # Otherwise, create Info from raw GraphQLResolveInfo
        if not hasattr(info, "_field"):
            info = _create_info_from_raw(info)  # type: ignore

        # Wrap _next to pass raw info to graphql-core
        def wrapped_next(root: Any, info: Info, *args: str, **kwargs: Any) -> Any:
            raw_info = info._raw_info
            return _next(root, raw_info, *args, **kwargs)

        return original_resolve(self, wrapped_next, root, info, *args, **kwargs)

    wrapped_resolve._strawberry_wrapped = True  # type: ignore
    return wrapped_resolve


def _wrap_resolve_with_deprecation(
    original_resolve: Callable,
) -> Callable:
    """Wrap a resolve method to convert Info to GraphQLResolveInfo with deprecation warning."""
    warned = False

    @functools.wraps(original_resolve)
    def wrapped_resolve(
        self: SchemaExtension,
        _next: Callable,
        root: Any,
        info: Info,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        nonlocal warned
        if not warned:
            warnings.warn(
                f"Extension {type(self).__name__} uses the deprecated "
                "GraphQLResolveInfo type hint for the 'info' parameter in resolve(). "
                "Please update to use strawberry.Info instead. "
                "GraphQLResolveInfo support will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2,
            )
            warned = True

        # If info is already an Info object, extract raw info
        # Otherwise, info is already raw (shouldn't happen with new wrapper chain)
        raw_info = info._raw_info if hasattr(info, "_raw_info") else info
        return original_resolve(self, _next, root, raw_info, *args, **kwargs)

    wrapped_resolve._strawberry_wrapped_for_deprecation = True  # type: ignore
    return wrapped_resolve


class LifecycleStep(Enum):
    OPERATION = "operation"
    VALIDATION = "validation"
    PARSE = "parse"
    RESOLVE = "resolve"


class SchemaExtension:
    execution_context: ExecutionContext

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Check if this subclass overrides resolve
        if "resolve" not in cls.__dict__:
            return

        original_resolve = cls.__dict__["resolve"]

        # Skip if already wrapped
        if getattr(original_resolve, "_strawberry_wrapped", False):
            return

        # Check if extension uses old signature (GraphQLResolveInfo)
        uses_old_signature = _check_uses_old_resolve_signature(
            cls, SchemaExtension.resolve
        )

        if uses_old_signature:
            # Old signature: wrap with deprecation wrapper first, then info wrapper
            # Order: raw_info -> info_wrapper(creates Info) -> deprecation_wrapper(extracts raw) -> extension
            wrapped = _wrap_resolve_with_deprecation(original_resolve)
            wrapped = _wrap_resolve_with_info(wrapped)
        else:
            # New signature: wrap with info wrapper only
            wrapped = _wrap_resolve_with_info(original_resolve)

        cls.resolve = wrapped  # type: ignore

    # to support extensions that still use the old signature
    # we have an optional argument here for ease of initialization.
    def __init__(
        self, *, execution_context: ExecutionContext | None = None
    ) -> None: ...
    def on_operation(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after a GraphQL operation (query / mutation) starts."""
        yield None

    def on_validate(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the validation step."""
        yield None

    def on_parse(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the parsing step."""
        yield None

    def on_execute(  # type: ignore
        self,
    ) -> AsyncIteratorOrIterator[None]:  # pragma: no cover
        """Called before and after the execution step."""
        yield None

    def resolve(
        self,
        _next: Callable,
        root: Any,
        info: Info,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        return _next(root, info, *args, **kwargs)

    def get_results(self) -> AwaitableOrValue[dict[str, Any]]:
        return {}

    @classmethod
    def _implements_resolve(cls) -> bool:
        """Whether the extension implements the resolve method."""
        return cls.resolve is not SchemaExtension.resolve


Hook = Callable[[SchemaExtension], AsyncIteratorOrIterator[None]]

HOOK_METHODS: set[str] = {
    SchemaExtension.on_operation.__name__,
    SchemaExtension.on_validate.__name__,
    SchemaExtension.on_parse.__name__,
    SchemaExtension.on_execute.__name__,
}

__all__ = ["HOOK_METHODS", "Hook", "LifecycleStep", "SchemaExtension"]
