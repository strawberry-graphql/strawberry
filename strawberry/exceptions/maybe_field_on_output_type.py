from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Literal

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from collections.abc import Callable

    from .exception_source import ExceptionSource


class MaybeFieldOnOutputTypeError(StrawberryException):
    """A field typed as `strawberry.Maybe` on a type or an interface.

    `Maybe` tells the fields a client left out apart from the ones it set to
    null, which only makes sense for inputs: GraphQL has no value for an output
    field that was left out, and the `Some` would be serialized as its repr.

    `resolver` is the resolver of the field, when it returns the `Maybe`.
    """

    def __init__(
        self,
        field_name: str,
        cls: type,
        *,
        kind: Literal["type", "interface"] = "type",
        resolver: Callable[..., object] | None = None,
    ) -> None:
        self.cls = cls
        self.field_name = field_name
        self.kind = kind
        self.resolver = resolver

        self.message = (
            f"Field `{field_name}` on {kind} `{cls.__name__}` can't use "
            "`strawberry.Maybe`"
        )
        self.rich_message = (
            f"Field `[underline]{field_name}[/]` on {kind} "
            f"`[underline]{cls.__name__}[/]` can't use `strawberry.Maybe`"
        )
        self.annotation_message = (
            "resolver returning strawberry.Maybe"
            if resolver is not None
            else "field typed as strawberry.Maybe"
        )
        example = (
            f"def {field_name}(self) -> str | None"
            if resolver is not None
            else f"{field_name}: str | None"
        )
        self.suggestion = (
            "`strawberry.Maybe` tells the fields a client left out apart from the "
            "ones it set to null, which only makes sense for inputs. Make the "
            f"field nullable instead, e.g. `{example}`."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        if self.resolver is not None and (
            source := source_finder.find_function_from_object(self.resolver)
        ):
            return source

        return source_finder.find_class_attribute_from_object(
            self.cls, self.field_name
        ) or source_finder.find_class_from_object(self.cls)
