from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import cached_property
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import TypeAlias

    from strawberry.types import Info
    from strawberry.types.field import StrawberryField


SyncExtensionResolver: TypeAlias = Callable[..., Any]
AsyncExtensionResolver: TypeAlias = Callable[..., Awaitable[Any]]


class FieldExtension:
    def apply(self, field: StrawberryField) -> None:  # pragma: no cover
        pass

    def resolve(
        self, next_: SyncExtensionResolver, source: Any, info: Info, **kwargs: Any
    ) -> Any:  # pragma: no cover
        raise NotImplementedError(
            "Sync Resolve is not supported for this Field Extension"
        )

    async def resolve_async(
        self, next_: AsyncExtensionResolver, source: Any, info: Info, **kwargs: Any
    ) -> Any:  # pragma: no cover
        raise NotImplementedError(
            "Async Resolve is not supported for this Field Extension"
        )

    @cached_property
    def supports_sync(self) -> bool:
        return type(self).resolve is not FieldExtension.resolve

    @cached_property
    def supports_async(self) -> bool:
        return type(self).resolve_async is not FieldExtension.resolve_async


class SyncToAsyncExtension(FieldExtension):
    """Helper class for mixing async extensions with sync resolvers.

    Applied automatically.
    """

    async def resolve_async(
        self, next_: AsyncExtensionResolver, source: Any, info: Info, **kwargs: Any
    ) -> Any:
        return next_(source, info, **kwargs)


def _get_sync_resolvers(
    extensions: list[FieldExtension],
) -> list[SyncExtensionResolver]:
    # List comprehension is already highly efficient, but avoid function call in hot path:
    # Use generator expression and list constructor to minimize exec overhead.
    return [e.resolve for e in extensions]


def _get_async_resolvers(
    extensions: list[FieldExtension],
) -> list[AsyncExtensionResolver]:
    # As above, return method references directly.
    return [e.resolve_async for e in extensions]


def build_field_extension_resolvers(
    field: StrawberryField,
) -> list[SyncExtensionResolver | AsyncExtensionResolver]:
    """Builds a list of resolvers for a field with extensions.

    Verifies that all of the field extensions for a given field support
    sync or async depending on the field resolver.

    Inserts a SyncToAsyncExtension to be able to use Async extensions on sync resolvers
    Throws a TypeError otherwise.

    Returns True if resolving should be async, False on sync resolving
    based on the resolver and extensions
    """
    extensions = field.extensions
    if not extensions:
        return []  # pragma: no cover

    # -- Optimization: single pass for async/sync checks, with memorized results --
    # Don't build entire non_async/non_sync lists unless needed; instead cache indexes and counts.
    # Using list comprehension for name construction can be done after, only if error is to be raised.

    # Pre-pass, gather: lists of indices of non-async and non-sync extensions
    non_async_extensions = []
    non_sync_extensions = []
    for ext in extensions:
        if not ext.supports_async:
            non_async_extensions.append(ext)
        if not ext.supports_sync:
            non_sync_extensions.append(ext)

    # These list comprehensions/joins are only required if an error must be raised
    if field.is_async:
        if non_async_extensions:
            non_async_extension_names = ",".join(
                ext.__class__.__name__ for ext in non_async_extensions
            )
            raise TypeError(
                f"Cannot add sync-only extension(s) {non_async_extension_names} "
                f"to the async resolver of Field {field.name}. "
                f"Please add a resolve_async method to the extension(s)."
            )
        # All extensions are async-compatible
        return _get_async_resolvers(extensions)

    if not non_sync_extensions:
        # All extensions are sync-compatible
        return _get_sync_resolvers(extensions)

    # Find cut index for prepending SyncToAsyncExtension
    found_sync_extensions = 0
    found_sync_only_extensions = 0
    non_async_exts_set = set(non_async_extensions)
    non_sync_exts_set = set(non_sync_extensions)
    # This for-loop is hot -- optimize by using set membership.
    # Short-circuit when finding first async-only extension
    for ext in extensions:
        if ext in non_sync_exts_set:
            break
        if ext in non_async_exts_set:
            found_sync_only_extensions += 1
        found_sync_extensions += 1

    if found_sync_only_extensions == len(non_async_extensions):
        # Precompute get_sync/_async slices, chain as before
        pre_sync = _get_sync_resolvers(extensions[:found_sync_extensions])
        post_async = _get_async_resolvers(extensions[found_sync_extensions:])
        # Compose into final resolver chain
        # Note: Chain is already lazy. List() forces realization, as expected return type
        return [
            *pre_sync,
            SyncToAsyncExtension().resolve_async,
            *post_async,
        ]

    # Some sync-only extension(s) are after the first async-only extension: error case
    async_extension_names = ",".join(
        ext.__class__.__name__ for ext in non_sync_extensions
    )
    non_async_extension_names = ",".join(
        ext.__class__.__name__ for ext in non_async_extensions
    )
    raise TypeError(
        f"Cannot mix async-only extension(s) {async_extension_names} "
        f"with sync-only extension(s) {non_async_extension_names} "
        f"on Field {field.name}. "
        f"If possible try to change the execution order so that all sync-only "
        f"extensions are executed first."
    )


__all__ = ["FieldExtension"]
