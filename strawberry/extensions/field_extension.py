from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from strawberry.utils.cached_property import cached_property

if TYPE_CHECKING:
    from strawberry.field import StrawberryField
    from strawberry.types import Info


class FieldExtension:
    def apply(self, field: StrawberryField) -> None:
        pass

    def resolve(self, next: Callable[..., Any], source: Any, info: Info, **kwargs):
        pass

    async def resolve_async(
        self, next: Callable[..., Any], source: Any, info: Info, **kwargs
    ):
        pass

    @cached_property
    def supports_sync(self):
        return type(self).resolve is not FieldExtension.resolve

    @cached_property
    def supports_async(self) -> bool:
        return type(self).resolve_async is not FieldExtension.resolve_async


def check_field_extension_compatibility(field: StrawberryField):
    """
    Verifies that all of the field extensions for a given field support
    sync or async depending on the field resolver.
    Throws a TypeError otherwise.
    """
    if not field.extensions or not len(field.extensions):
        return

    if field.is_async:
        non_async_extensions = list(
            filter(lambda extension: not extension.supports_async, field.extensions)
        )
        if len(non_async_extensions) > 0:
            extension_names = ",".join(
                [extension.__class__.__name__ for extension in non_async_extensions]
            )
            raise TypeError(
                f"Cannot add sync-only extension(s) {extension_names} "
                f"to the async resolver of Field {field.name}. "
                f"Please add a resolve_async method to the extension."
            )
    else:
        non_sync_extensions = list(
            filter(lambda extension: not extension.supports_sync, field.extensions)
        )
        if len(non_sync_extensions) > 0:
            extension_names = ",".join(
                [extension.__class__.__name__ for extension in non_sync_extensions]
            )
            raise TypeError(
                f"Cannot add async-only extension(s) {extension_names} "
                f"to the sync resolver of Field {field.name}. "
                f"Please add a resolve method to the extension."
            )
