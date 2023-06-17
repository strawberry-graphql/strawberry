from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from strawberry.utils.cached_property import cached_property

from .exception import StrawberryException

if TYPE_CHECKING:
    from ..field import StrawberryField
    from .exception_source import ExceptionSource


class PermissionFailSilentlyRequiresOptionalError(StrawberryException):
    def __init__(self, field: StrawberryField):
        self.message = (
            "Cannot use fail_silently=True with a non-optional " "or non-list field"
        )
        self.rich_message = (
            "fail_silently permissions can only be used with fields of type "
            f"optional or list. Provided field `[underline]{field.name}[/]` "
            f"is of type `[underline]{field.type}[/]`"
        )
        self.annotation_message = "field defined here"
        self.suggestion = (
            "To fix this error, make sure you apply use `fail_silently`"
            " on a field that is either a list or nullable."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        # we can't return an exception source as currently, permission
        # extensions are only linked
        # to strawberryfields. these aren't linked to the source code.
        return None
