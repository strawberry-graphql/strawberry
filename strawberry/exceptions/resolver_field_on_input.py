from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from .exception import StrawberryException
from .utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from strawberry.types.field import StrawberryField

    from .exception_source import ExceptionSource


class ResolverFieldOnInputError(StrawberryException):
    """A field with a resolver on an input type.

    Input types only hold the values sent by the client, so the resolver would
    never run, and requests using the input would fail, as the field can't be
    passed to the input type.

    `inherited_from` is the base type the field comes from, if it's inherited.
    """

    def __init__(
        self,
        field_name: str,
        cls: type,
        resolver_field: StrawberryField,
        inherited_from: type | None = None,
    ) -> None:
        self.cls = cls
        self.field_name = field_name
        self.resolver_field = resolver_field
        self.inherited_from = inherited_from

        inherited = (
            f", inherited from `{inherited_from.__name__}`,"
            if inherited_from is not None
            else ""
        )
        rich_inherited = (
            f", inherited from `[underline]{inherited_from.__name__}[/]`,"
            if inherited_from is not None
            else ""
        )

        self.message = (
            f"Field `{field_name}` on input type `{cls.__name__}`{inherited} can't "
            "have a resolver"
        )
        self.rich_message = (
            f"Field `[underline]{field_name}[/]` on input type "
            f"`[underline]{cls.__name__}[/]`{rich_inherited} can't have a resolver"
        )
        self.annotation_message = "field with a resolver"

        if inherited_from is None:
            self.suggestion = (
                "Input types only hold the values sent by the client, so remove "
                "the resolver, or move the field to an output type."
            )
        else:
            self.suggestion = (
                "Input types only hold the values sent by the client, so they "
                "can't inherit fields with resolvers. Move the fields to share to "
                f"a base type without resolvers, which both `{cls.__name__}` and "
                f"`{inherited_from.__name__}` inherit from."
            )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        if (resolver := self.resolver_field.base_resolver) is not None and (
            source := source_finder.find_function_from_object(
                resolver._unbound_wrapped_func
            )
        ):
            return source

        # e.g. a lambda passed as `strawberry.field(resolver=...)`
        return source_finder.find_class_attribute_from_object(
            self.inherited_from or self.cls, self.field_name
        ) or source_finder.find_class_from_object(self.cls)
