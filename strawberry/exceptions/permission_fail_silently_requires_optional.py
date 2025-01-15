from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from strawberry.field import StrawberryField

    from .exception_source import ExceptionSource


class PermissionFailSilentlyRequiresOptionalError(StrawberryException):
    def __init__(self, field: StrawberryField) -> None:
        self.field = field
        self.message = (
            "Cannot use fail_silently=True with a non-optional or non-list field"
        )
        self.rich_message = (
            "fail_silently permissions can only be used with fields of type "
            f"optional or list. Provided field `[underline]{field.name}[/]` "
            f"is of type `[underline]{field.type.__name__}[/]`"
        )
        self.annotation_message = "field defined here"
        self.suggestion = (
            "To fix this error, make sure you apply use `fail_silently`"
            " on a field that is either a list or nullable."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> Optional[ExceptionSource]:
        origin = self.field.origin
        source_finder = SourceFinder()

        source = None
        if origin is not None:
            source = source_finder.find_class_attribute_from_object(
                origin,
                self.field.python_name,
            )

        # in case it is a function
        if source is None and self.field.base_resolver is not None:
            source = source_finder.find_function_from_object(
                self.field.base_resolver.wrapped_func
            )

        return source
