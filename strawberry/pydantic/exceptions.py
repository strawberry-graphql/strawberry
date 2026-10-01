from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from strawberry.exceptions.exception import StrawberryException
from strawberry.exceptions.utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from pydantic import BaseModel

    from strawberry.exceptions.exception_source import ExceptionSource
    from strawberry.types.field import StrawberryField


class UnregisteredTypeException(Exception):
    """A pydantic model used by a field isn't a Strawberry type."""

    def __init__(
        self,
        type: type[BaseModel],
        *,
        cls: type | None = None,
        field_name: str | None = None,
        is_input: bool = False,
    ) -> None:
        self.type = type

        decorator = "input" if is_input else "type"
        location = (
            f"`{cls.__name__}.{field_name}` uses `{type.__name__}`, which"
            if cls is not None and field_name is not None
            else f"`{type.__name__}`"
        )

        super().__init__(
            f"{location} isn't a Strawberry type: decorate it with "
            f"`@strawberry.pydantic.{decorator}`"
        )


class StrawberryFieldAsDefaultError(StrawberryException):
    def __init__(self, field_name: str, cls: type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f"`strawberry.field()` can't be used as the default value of field "
            f"`{field_name}` on pydantic model `{cls.__name__}`"
        )
        self.rich_message = (
            f"`strawberry.field()` can't be used as the default value of field "
            f"`[underline]{field_name}[/]` on pydantic model "
            f"`[underline]{cls.__name__}[/]`"
        )
        self.annotation_message = "strawberry.field() used as a default value"
        self.suggestion = (
            "Pydantic keeps only the default of a `strawberry.field()` assigned to "
            "a field and discards the rest of its configuration. Move it into the "
            f"annotation instead: `{field_name}: Annotated[..., strawberry.field(...)]`."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)


class UploadFieldError(StrawberryException):
    def __init__(self, field_name: str, cls: type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f"Field `{field_name}` on pydantic input `{cls.__name__}` can't be typed "
            "as `Upload`"
        )
        self.rich_message = (
            f"Field `[underline]{field_name}[/]` on pydantic input "
            f"`[underline]{cls.__name__}[/]` can't be typed as `Upload`"
        )
        self.annotation_message = "field typed as Upload"
        self.suggestion = (
            "Uploaded files are the file objects of your integration, which "
            "Pydantic can't validate as `Upload`. Annotate the field with the file "
            "type and use `Upload` as its GraphQL type, for example: "
            f"`{field_name}: Annotated[UploadFile, "
            "strawberry.field(graphql_type=Upload)]` "
            "(with `arbitrary_types_allowed=True` in `model_config`)."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)


class NotAPydanticModelError(StrawberryException):
    def __init__(self, obj: object, decorator: str) -> None:
        self.obj = obj

        obj_name = getattr(obj, "__name__", repr(obj))
        is_pydantic_v1_model = isinstance(obj, type) and any(
            base.__module__.startswith("pydantic.v1") for base in obj.__mro__
        )

        if is_pydantic_v1_model:
            self.message = (
                f"`{obj_name}` is a pydantic v1 model, but strawberry.pydantic."
                f"{decorator} only supports pydantic v2 models"
            )
            self.suggestion = (
                "Migrate the model to pydantic v2 (`from pydantic import "
                "BaseModel`), or use `strawberry.experimental.pydantic`, which "
                "supports pydantic v1 models."
            )
        else:
            self.message = (
                f"strawberry.pydantic.{decorator} can only be used with pydantic "
                f"models, but `{obj_name}` is not a subclass of `pydantic.BaseModel`"
            )
            self.suggestion = (
                f"Use `strawberry.{decorator}` for classes that aren't pydantic models."
            )

        self.rich_message = self.message
        self.annotation_message = "class defined here"

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        if not isinstance(self.obj, type):
            return None

        return SourceFinder().find_class_from_object(self.obj)


class MaybeFieldError(StrawberryException):
    def __init__(self, field_name: str, cls: type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f"Field `{field_name}` on pydantic input `{cls.__name__}` can't use "
            "`strawberry.Maybe`"
        )
        self.rich_message = (
            f"Field `[underline]{field_name}[/]` on pydantic input "
            f"`[underline]{cls.__name__}[/]` can't use `strawberry.Maybe`"
        )
        self.annotation_message = "field typed as strawberry.Maybe"
        self.suggestion = (
            "Pydantic inputs tell omitted fields apart from explicit nulls with "
            "`model_fields_set`: give the field a `None` default, e.g. "
            f"`{field_name}: str | None = None`, and use "
            "`model_dump(exclude_unset=True)` to get the fields the client sent."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)


class ResolverFieldOnInputError(StrawberryException):
    def __init__(
        self, field_name: str, cls: type, resolver_field: StrawberryField
    ) -> None:
        self.cls = cls
        self.field_name = field_name
        self.resolver_field = resolver_field

        self.message = (
            f"Field `{field_name}` on pydantic input `{cls.__name__}` can't have a "
            "resolver"
        )
        self.rich_message = (
            f"Field `[underline]{field_name}[/]` on pydantic input "
            f"`[underline]{cls.__name__}[/]` can't have a resolver"
        )
        self.annotation_message = "field with a resolver"
        self.suggestion = (
            "Input types only hold the values sent by the client, so remove the "
            "resolver, or move the field to an output type."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        if self.resolver_field.base_resolver is not None:
            return source_finder.find_function_from_object(
                self.resolver_field.base_resolver._unbound_wrapped_func
            )

        return source_finder.find_class_from_object(self.cls)


class ResolverFieldOverridesModelFieldError(StrawberryException):
    def __init__(self, field_name: str, cls: type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f"The resolver of `{field_name}` on pydantic model `{cls.__name__}` "
            f"overrides a model field with the same name"
        )
        self.rich_message = (
            f"The resolver of `[underline]{field_name}[/]` on pydantic model "
            f"`[underline]{cls.__name__}[/]` overrides a model field with the same "
            "name"
        )
        self.annotation_message = "resolver with the name of a model field"
        self.suggestion = (
            "Pydantic would use the resolver as the default value of the field. "
            "Rename the resolver, or remove the model field."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        return SourceFinder().find_class_attribute_from_object(
            self.cls, self.field_name
        )


class ModelAlreadyDecoratedError(StrawberryException):
    def __init__(self, cls: type, decorator: str) -> None:
        self.cls = cls

        definition = cls.__strawberry_definition__  # type: ignore[attr-defined]
        kind = (
            "an input"
            if definition.is_input
            else "an interface"
            if definition.is_interface
            else "a type"
        )

        self.message = (
            f"`{cls.__name__}` is already {kind}, so it can't be decorated with "
            f"`strawberry.pydantic.{decorator}`"
        )
        self.rich_message = (
            f"`[underline]{cls.__name__}[/]` is already {kind}, so it can't be "
            f"decorated with `strawberry.pydantic.{decorator}`"
        )
        self.annotation_message = "model decorated twice"

        if definition.is_input == (decorator == "input"):
            self.suggestion = "Remove one of the decorators."
        else:
            self.suggestion = (
                "To use a model both as an output type and as an input, decorate "
                "a subclass, for example: `@strawberry.pydantic.input class "
                "AddressInput(Address): pass`."
            )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        return SourceFinder().find_class_from_object(self.cls)
