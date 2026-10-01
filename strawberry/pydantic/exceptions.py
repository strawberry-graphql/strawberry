from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from strawberry.exceptions.exception import StrawberryException
from strawberry.exceptions.utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from pydantic import BaseModel

    from strawberry.exceptions.exception_source import ExceptionSource


class UnregisteredTypeException(Exception):
    def __init__(self, type: type[BaseModel]) -> None:
        message = (
            f"Cannot find a Strawberry Type for {type} did you forget to register it?"
        )

        super().__init__(message)


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
