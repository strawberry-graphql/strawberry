from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .exception_source import ExceptionSource


class UnresolvedStrawberryFieldError(StrawberryException):
    def __init__(
        self,
        field_name: str,
        cls: type,
        undefined_names: Sequence[str],
        *,
        in_options: bool = False,
    ) -> None:
        self.cls = cls
        self.field_name = field_name

        names = ", ".join(f"`{name}`" for name in undefined_names)

        if len(undefined_names) == 1:
            reason = f"{names} isn't defined yet"
        elif undefined_names:
            reason = f"{names} aren't defined yet"
        else:
            reason = "its annotation can't be evaluated yet"

        self.message = (
            f"The `strawberry.field()` options of field `{field_name}` on type "
            f"`{cls.__name__}` can't be read, because {reason}"
        )
        self.rich_message = (
            f"The `strawberry.field()` options of field `[underline]{field_name}[/]` "
            f"on type `[underline]{cls.__name__}[/]` can't be read, because {reason}"
        )
        self.annotation_message = "annotation using names that aren't defined yet"
        if in_options:
            # e.g. a permission class defined after the type
            self.suggestion = (
                "The options are evaluated when the type is created, so define "
                f"the names they use before `{cls.__name__}`."
            )
        else:
            self.suggestion = (
                "Before Python 3.14, Strawberry can only read the options of an "
                "annotation it can evaluate when the type is created. Pass the "
                f"options as the field's default instead, like `{field_name}: ... "
                "= strawberry.field(...)`, define the types it uses before "
                f"`{cls.__name__}`, or use `strawberry.lazy()` for them."
            )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)
