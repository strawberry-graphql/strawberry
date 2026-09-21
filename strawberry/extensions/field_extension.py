from __future__ import annotations

import itertools
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

    def map_arguments(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Reshape the resolver's keyword arguments after they are converted.

        Called during argument conversion, before the resolver (and the resolve
        chain) runs, and only when conversion succeeds. Extensions that change a
        field's argument shape (e.g. ``InputMutationExtension``) use this instead
        of a resolve wrapper, so they never see the un-converted arguments passed
        along the argument-conversion-error path.
        """
        return kwargs

    @cached_property
    def supports_sync(self) -> bool:
        return type(self).resolve is not FieldExtension.resolve

    @cached_property
    def supports_async(self) -> bool:
        return type(self).resolve_async is not FieldExtension.resolve_async

    @cached_property
    def has_resolver(self) -> bool:
        """Whether the extension takes part in the resolve chain.

        Extensions that implement neither ``resolve`` nor ``resolve_async`` only
        hook into ``apply``/``map_arguments`` and are left out of the chain.
        """
        return self.supports_sync or self.supports_async


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
    return [extension.resolve for extension in extensions]


def _get_async_resolvers(
    extensions: list[FieldExtension],
) -> list[AsyncExtensionResolver]:
    return [extension.resolve_async for extension in extensions]


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
    if not field.extensions:
        return []  # pragma: no cover

    # Extensions that only hook into ``apply``/``map_arguments`` (no ``resolve``
    # or ``resolve_async``) take no part in the resolve chain, so leave them out.
    extensions = [extension for extension in field.extensions if extension.has_resolver]
    if not extensions:
        return []

    non_async_extensions = [
        extension for extension in extensions if not extension.supports_async
    ]
    non_async_extension_names = ",".join(
        [extension.__class__.__name__ for extension in non_async_extensions]
    )

    if field.is_async:
        if len(non_async_extensions) > 0:
            raise TypeError(
                f"Cannot add sync-only extension(s) {non_async_extension_names} "
                f"to the async resolver of Field {field.name}. "
                f"Please add a resolve_async method to the extension(s)."
            )
        return _get_async_resolvers(extensions)
    # Try to wrap all sync resolvers in async so that we can use async extensions
    # on sync fields. This is not possible the other way around since
    # the result of an async resolver would have to be awaited before calling
    # the sync extension, making it impossible for the extension to modify
    # any arguments.
    non_sync_extensions = [
        extension for extension in extensions if not extension.supports_sync
    ]

    if len(non_sync_extensions) == 0:
        # Resolve everything sync
        return _get_sync_resolvers(extensions)

    # We have async-only extensions and need to wrap the resolver
    # That means we can't have sync-only extensions after the first async one

    # Check if we have a chain of sync-compatible
    # extensions before the async extensions
    # -> S-S-S-S-A-A-A-A
    found_sync_extensions = 0

    # All sync only extensions must be found before the first async-only one
    found_sync_only_extensions = 0
    for extension in extensions:
        # ...A, abort
        if extension in non_sync_extensions:
            break
        # ...S
        if extension in non_async_extensions:
            found_sync_only_extensions += 1
        found_sync_extensions += 1

    # Length of the chain equals length of non async extensions
    # All sync extensions run first
    if len(non_async_extensions) == found_sync_only_extensions:
        # Prepend sync to async extension to field extensions
        return list(
            itertools.chain(
                _get_sync_resolvers(extensions[:found_sync_extensions]),
                [SyncToAsyncExtension().resolve_async],
                _get_async_resolvers(extensions[found_sync_extensions:]),
            )
        )

    # Some sync extensions follow the first async-only extension. Error case
    async_extension_names = ",".join(
        [extension.__class__.__name__ for extension in non_sync_extensions]
    )
    raise TypeError(
        f"Cannot mix async-only extension(s) {async_extension_names} "
        f"with sync-only extension(s) {non_async_extension_names} "
        f"on Field {field.name}. "
        f"If possible try to change the execution order so that all sync-only "
        f"extensions are executed first."
    )


__all__ = ["FieldExtension"]
