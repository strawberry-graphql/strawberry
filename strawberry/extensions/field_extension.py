from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from strawberry.utils.cached_property import cached_property

if TYPE_CHECKING:
    from strawberry.field import StrawberryField
    from strawberry.types import Info


class FieldExtension:
    def apply(self, field: StrawberryField) -> None:  # nocov
        pass

    def resolve(
        self, next: Callable[..., Any], source: Any, info: Info, **kwargs
    ) -> Any:  # nocov
        raise NotImplementedError(
            "Sync Resolve is not supported for this Field Extension"
        )

    async def resolve_async(
        self, next: Callable[..., Any], source: Any, info: Info, **kwargs
    ) -> Any:  # nocov
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
    Applied automatically"""

    async def resolve_async(
        self, next: Callable[..., Any], source: Any, info: Info, **kwargs
    ) -> Any:  # nocov
        return next(source, info, **kwargs)


def ensure_field_extension_compatibility(field: StrawberryField) -> bool:
    """
    Verifies that all of the field extensions for a given field support
    sync or async depending on the field resolver.
    Inserts a SyncToAsyncExtension to be able to
    use Async extensions on sync resolvers
    Throws a TypeError otherwise.

    Returns True if resolving should be async, False on sync resolving
    based on the resolver and extensions
    """
    if not field.extensions or not len(field.extensions):  # nocov
        return field.is_async

    non_async_extensions = [
        extension for extension in field.extensions if not extension.supports_async
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
        return True
    else:
        # Try to wrap all sync resolvers in async so that we can use async extensions
        # on sync fields. This is not possible the other way around since
        # the result of an async resolver would have to be awaited before calling
        # the sync extension, making it impossible for the extension to modify
        # any arguments.
        non_sync_extensions = [
            extension for extension in field.extensions if not extension.supports_sync
        ]

        if len(non_sync_extensions) == 0:
            return False

        # We have async-only extensions and need to wrap the resolver
        # That means we can't have sync-only extensions anymore
        if len(non_async_extensions) > 0:
            async_extension_names = ",".join(
                [extension.__class__.__name__ for extension in non_sync_extensions]
            )
            raise TypeError(
                f"Cannot mix async-only extension(s) {async_extension_names} "
                f"with sync-only extension(s) {non_async_extension_names} "
                f"on Field {field.name}."
            )

        # Prepend sync to async extension to field extensions
        field.extensions.insert(0, SyncToAsyncExtension())
        return True
