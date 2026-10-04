from __future__ import annotations

import functools
import inspect
import re
from functools import cached_property
from typing import TYPE_CHECKING, Any, get_args, get_origin

from pydantic import BaseModel

from strawberry.exceptions.exception import StrawberryException
from strawberry.exceptions.utils.source_finder import SourceFinder

if TYPE_CHECKING:
    from collections.abc import Callable

    from strawberry.exceptions.exception_source import ExceptionSource
    from strawberry.types.field import StrawberryField


_MARKUP_TAG = re.compile(r"(\\*)(\[[a-z#/@][^[]*?])")


def _escape_markup(text: str) -> str:
    """Escape text that rich would read as markup, like `RootModel[list[str]]`.

    The same as `rich.markup.escape`, as rich is an optional dependency.
    """
    text = _MARKUP_TAG.sub(r"\1\1\\\2", text)

    if text.endswith("\\") and not text.endswith("\\\\"):
        text += "\\"

    return text


def _format_base(base: Any) -> str:
    """Return a base class like it's written in a class statement."""
    if args := get_args(base):
        # e.g. `Generic[T]`
        origin = _format_base(get_origin(base))

        return f"{origin}[{', '.join(_format_base(arg) for arg in args)}]"

    return getattr(base, "__name__", repr(base))


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
    def __init__(
        self, type_: type[BaseModel], *, cls: type, field_name: str, is_input: bool
    ) -> None:
        self.type = type_
        self.cls = cls
        self.field_name = field_name

        decorator = f"@strawberry.pydantic.{'input' if is_input else 'type'}"

        self.message = (
            f"`{cls.__name__}.{field_name}` uses `{type_.__name__}`, which isn't a "
            f"Strawberry type: decorate it with `{decorator}`"
        )
        # the names of parametrized generic models, like `Box[str]`, look like
        # rich markup
        type_name = _escape_markup(type_.__name__)

        self.rich_message = (
            f"`[underline]{cls.__name__}.{field_name}[/]` uses "
            f"`[underline]{type_name}[/]`, which isn't a Strawberry type"
        )
        self.annotation_message = f"field using {type_name}"
        self.suggestion = f"Decorate `{type_name}` with `{decorator}`."

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        return _find_field_source(self.cls, self.field_name)


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


class PydanticFieldWithoutResolverError(StrawberryException):
    def __init__(self, field_name: str, cls: type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f"Field `{field_name}` on pydantic model `{cls.__name__}` uses "
            "`strawberry.pydantic.field`, which is only for fields with a resolver"
        )
        self.rich_message = (
            f"Field `[underline]{field_name}[/]` on pydantic model "
            f"`[underline]{cls.__name__}[/]` uses `strawberry.pydantic.field`, "
            "which is only for fields with a resolver"
        )
        self.annotation_message = "strawberry.pydantic.field used on a model field"
        self.suggestion = (
            "`strawberry.pydantic.field` decorates methods to add fields with a "
            "resolver. To configure a model field, use `strawberry.field()` in its "
            f"annotation instead: `{field_name}: Annotated[..., "
            "strawberry.field(...)]`."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        return _find_field_source(self.cls, self.field_name)


class UnresolvedAnnotatedFieldError(StrawberryException):
    """The `Annotated` options of a field can't be read yet.

    `cls` declares the field, and `model` is the decorated model, which can be a
    subclass of it.
    """

    def __init__(self, field_name: str, cls: type, *, model: type) -> None:
        self.cls = cls
        self.field_name = field_name

        self.message = (
            f"The `Annotated` options of field `{field_name}` on pydantic model "
            f"`{cls.__name__}` can't be read because its annotation uses names "
            "that aren't defined yet"
        )
        self.rich_message = (
            f"The `Annotated` options of field `[underline]{field_name}[/]` on "
            f"pydantic model `[underline]{cls.__name__}[/]` can't be read because "
            "its annotation uses names that aren't defined yet"
        )
        self.annotation_message = "annotation using names that aren't defined yet"
        self.suggestion = (
            "Strawberry reads the options when the model is decorated, but Pydantic "
            "only reads them once it can resolve the annotation, so options like "
            "the permissions of `strawberry.field()` or `Field(exclude=True)` "
            "would be lost. Define the models the annotation references before "
            f"`{cls.__name__}`, or decorate `{model.__name__}` later: once they're "
            f"defined, call `{model.__name__}.model_rebuild()` and then decorate "
            "it. In a module without `from __future__ import annotations`, you can "
            'also quote only the types, like `Annotated["Account", '
            "strawberry.field(...)]`."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        return _find_field_source(self.cls, self.field_name)


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


class UnsupportedRootModelError(StrawberryException):
    """A `RootModel` is decorated, or used by a field of a pydantic type."""

    def __init__(
        self,
        root_model: type,
        *,
        decorator: str | None = None,
        cls: type | None = None,
        field_name: str | None = None,
    ) -> None:
        self.root_model = root_model
        self.cls = cls
        self.field_name = field_name

        # parametrized root models are named like `RootModel[list[int]]`
        name = root_model.__name__
        rich_name = _escape_markup(name)

        if cls is not None and field_name is not None:
            self.message = (
                f"`{cls.__name__}.{field_name}` uses `{name}`, which is a "
                "`RootModel` and can't be a GraphQL type"
            )
            self.rich_message = (
                f"`[underline]{cls.__name__}.{field_name}[/]` uses "
                f"`[underline]{rich_name}[/]`, which is a `RootModel` and can't be "
                "a GraphQL type"
            )
            self.annotation_message = f"field using {rich_name}"
        else:
            self.message = (
                f"`{name}` is a `RootModel`, which can't be used with "
                f"`strawberry.pydantic.{decorator}`"
            )
            self.rich_message = (
                f"`[underline]{rich_name}[/]` is a `RootModel`, which can't be used "
                f"with `strawberry.pydantic.{decorator}`"
            )
            self.annotation_message = "RootModel defined here"

        self.suggestion = _escape_markup(
            "A `RootModel` holds a single value instead of fields, so it can't be "
            "a GraphQL object type. Use the type of its value instead, for example "
            "`list[str]` for `RootModel[list[str]]`."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        if self.cls is not None and self.field_name is not None:
            return _find_field_source(self.cls, self.field_name)

        return SourceFinder().find_class_from_object(self.root_model)


class UnsupportedRelayNodeError(StrawberryException):
    def __init__(self, cls: type, decorator: str) -> None:
        self.cls = cls

        self.message = (
            f"`{cls.__name__}` implements `relay.Node`, which isn't supported by "
            f"`strawberry.pydantic.{decorator}` yet"
        )
        self.rich_message = (
            f"`[underline]{cls.__name__}[/]` implements `relay.Node`, which isn't "
            f"supported by `strawberry.pydantic.{decorator}` yet"
        )
        self.annotation_message = "model implementing relay.Node"
        self.suggestion = (
            "Pydantic types don't get the `id` field that `relay.Node` resolves "
            "from the `relay.NodeID` field. Use a `@strawberry.type` that "
            "implements `relay.Node` for the node instead, and create it from the "
            f"model, e.g. with `{cls.__name__}(**dict(model))`. Pydantic types can "
            "still be the nodes of connections, like `relay.ListConnection`."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        return SourceFinder().find_class_from_object(self.cls)


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


class ResolverAlreadyUsedError(StrawberryException):
    def __init__(self, resolver: Callable[..., Any]) -> None:
        self.resolver = resolver

        name = getattr(resolver, "__name__", repr(resolver))

        self.message = (
            f"`{name}` is already the resolver of a field, a resolver can only be "
            "used by one `strawberry.pydantic.field`"
        )
        self.rich_message = (
            f"`[underline]{name}[/]` is already the resolver of a field, a resolver "
            "can only be used by one `strawberry.pydantic.field`"
        )
        self.annotation_message = "resolver used by more than one field"
        self.suggestion = (
            "`strawberry.pydantic.field` stores the field on the function, so each "
            f"field needs its own function. Add a function that calls `{name}` for "
            "the other field."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        resolver = self.resolver

        if isinstance(resolver, (staticmethod, classmethod)):
            resolver = resolver.__func__

        if not inspect.isfunction(resolver):
            return None

        return SourceFinder().find_function_from_object(resolver)


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
        elif decorator == "input" and (
            definition.is_interface or definition.interfaces
        ):
            # a subclass would inherit the interface, and inputs can't implement
            # interfaces
            name = cls.__name__
            # `__orig_bases__` has the parameters of generic bases, like
            # `Generic[T]`, it's only set when there are some
            bases = ", ".join(
                [
                    f"{name}Base",
                    *(
                        _format_base(base)
                        for base in vars(cls).get("__orig_bases__", cls.__bases__)
                        if base is not BaseModel
                    ),
                ]
            )
            current_decorator = "interface" if definition.is_interface else "type"

            self.suggestion = _escape_markup(
                f"Inputs can't implement interfaces, so `{name}` can't be "
                "subclassed for an input. Move the fields to share to an "
                "undecorated base model used by both instead, for example: "
                f"`class {name}Base(BaseModel)`, with "
                f"`@strawberry.pydantic.{current_decorator} class {name}({bases})` "
                f"and `@strawberry.pydantic.input class {name}Input({name}Base)`."
            )
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
