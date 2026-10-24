from __future__ import annotations

import functools
import re
from functools import cached_property
from typing import TYPE_CHECKING

from strawberry.exceptions.exception import StrawberryException
from strawberry.exceptions.utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from pydantic import BaseModel

    from strawberry.exceptions.exception_source import ExceptionSource


_MARKUP_TAG = re.compile(r"(\\*)(\[[a-z#/@][^[]*?])")


def _escape_markup(text: str) -> str:
    """Escape text that rich would read as markup, like `RootModel[list[str]]`.

    The same as `rich.markup.escape`, as rich is an optional dependency.
    """
    text = _MARKUP_TAG.sub(r"\1\1\\\2", text)

    if text.endswith("\\") and not text.endswith("\\\\"):
        text += "\\"

    return text


def _find_field_source(cls: type, field_name: str) -> ExceptionSource | None:
    source_finder = SourceFinder()
    attribute = vars(cls).get(field_name)

    # computed fields are properties, not annotated attributes
    if isinstance(attribute, property):
        getter = attribute.fget
    elif isinstance(attribute, functools.cached_property):
        getter = attribute.func
    else:
        return source_finder.find_class_attribute_from_object(cls, field_name)

    return source_finder.find_function_from_object(getter) if getter else None


class UnregisteredPydanticTypeError(StrawberryException):
    def __init__(self, type_: type[BaseModel], *, cls: type, field_name: str) -> None:
        self.type = type_
        self.cls = cls
        self.field_name = field_name

        decorator = "@strawberry.pydantic.type"
        generic_metadata = getattr(type_, "__pydantic_generic_metadata__", {})
        # the decorated base the model inherits its definition from, which
        # isn't its own GraphQL type
        decorated_base = next(
            (
                base
                for base in type_.__mro__[1:]
                if "__strawberry_definition__" in vars(base)
            ),
            None,
        )

        if generic_metadata.get("origin") is not None:
            # e.g. `Page[User]`, which pydantic creates when it's used
            origin = generic_metadata["origin"].__name__
            subclass = "".join(
                [
                    *(getattr(arg, "__name__", "") for arg in generic_metadata["args"]),
                    origin,
                ]
            )
            problem = "a parametrized generic model, which can't be a GraphQL type"
            fix = f"decorate a subclass of it with `{decorator}`"
            suggestion = (
                f"Decorate a subclass of it instead, for example: `{decorator} "
                f"class {subclass}({type_.__name__}): pass`."
            )
        elif decorated_base is not None:
            problem = (
                "which isn't a Strawberry type, even though it extends "
                f"`{decorated_base.__name__}`"
            )
            fix = f"decorate it with `{decorator}`"
            suggestion = (
                f"Subclasses of decorated models need their own decorator: "
                f"decorate `{type_.__name__}` with `{decorator}`, or use "
                f"`{decorated_base.__name__}` for the field."
            )
        else:
            problem = "which isn't a Strawberry type"
            fix = f"decorate it with `{decorator}`"
            suggestion = f"Decorate `{type_.__name__}` with `{decorator}`."

        self.message = (
            f"`{cls.__name__}.{field_name}` uses `{type_.__name__}`, {problem}: {fix}"
        )
        # the names of parametrized generic models, like `Box[str]`, look like
        # rich markup
        type_name = _escape_markup(type_.__name__)

        self.rich_message = (
            f"`[underline]{cls.__name__}.{field_name}[/]` uses "
            f"`[underline]{type_name}[/]`, {_escape_markup(problem)}"
        )
        self.annotation_message = f"field using {type_name}"
        self.suggestion = _escape_markup(suggestion)

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        return _find_field_source(self.cls, self.field_name)


class MisplacedFieldError(StrawberryException):
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

        self.suggestion = "Remove one of the decorators."

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        return SourceFinder().find_class_from_object(self.cls)
