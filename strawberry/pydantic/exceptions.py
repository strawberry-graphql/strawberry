from __future__ import annotations

import functools
import inspect
import re
from functools import cached_property
from typing import TYPE_CHECKING, Any, Literal, get_args, get_origin

from pydantic import BaseModel

from strawberry.exceptions.exception import StrawberryException
from strawberry.exceptions.utils.source_finder import SourceFinder
from strawberry.types.base import has_object_definition

if TYPE_CHECKING:

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


def _is_undecorated_model(base: Any) -> bool:
    """Whether a base class is a pydantic model without a GraphQL definition."""
    return (
        isinstance(base, type)
        and issubclass(base, BaseModel)
        and base is not BaseModel
        and not has_object_definition(base)
    )


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


def _format_message(template: str, **names: str) -> tuple[str, str]:
    """Format an error message, and its rich version with the names underlined."""
    underlined = {key: f"[underline]{value}[/]" for key, value in names.items()}

    return template.format(**names), template.format(**underlined)


class UnregisteredPydanticTypeError(StrawberryException):
    def __init__(
        self, type_: type[BaseModel], *, cls: type, field_name: str, is_input: bool
    ) -> None:
        self.type = type_
        self.cls = cls
        self.field_name = field_name

        decorator = f"@strawberry.pydantic.{'input' if is_input else 'type'}"
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
    def __init__(
        self,
        field_name: str,
        cls: type,
        *,
        usage: Literal["default", "model_field", "resolver"],
        field: StrawberryField | None = None,
    ) -> None:
        self.cls = cls
        self.field_name = field_name
        self.field = field

        if usage == "default":
            template = (
                "`strawberry.field()` can't be used as the default value of field "
                "`{field}` on pydantic model `{cls}`"
            )
            self.annotation_message = "strawberry.field() used as a default value"
            self.suggestion = (
                "Pydantic keeps only the default of a `strawberry.field()` assigned "
                "to a field and discards the rest of its configuration. Move it into "
                f"the annotation instead: `{field_name}: Annotated[..., "
                "strawberry.field(...)]`."
            )
        elif usage == "model_field":
            template = (
                "Field `{field}` on pydantic model `{cls}` uses "
                "`strawberry.pydantic.field`, which is only for fields with a resolver"
            )
            self.annotation_message = "strawberry.pydantic.field used on a model field"
            self.suggestion = (
                "`strawberry.pydantic.field` decorates methods to add fields with a "
                "resolver. To configure a model field, use `strawberry.field()` in its "
                f"annotation instead: `{field_name}: Annotated[..., "
                "strawberry.field(...)]`."
            )
        else:
            is_model = issubclass(cls, BaseModel)
            kind = "pydantic model" if is_model else "class"

            template = (
                f"Field `{{field}}` on {kind} `{{cls}}` uses `strawberry.field`, "
                "which pydantic types only read from Strawberry types and interfaces"
            )
            self.annotation_message = "strawberry.field outside of a Strawberry type"
            self.suggestion = (
                "Use `@strawberry.pydantic.field` to add a field with a resolver to a "
                "pydantic model."
                if is_model
                else "Use `@strawberry.pydantic.field`, or decorate "
                f"`{cls.__name__}` with `@strawberry.type` or `@strawberry.interface`."
            )

        self.message, self.rich_message = _format_message(
            template, field=field_name, cls=cls.__name__
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        resolver = self.field.base_resolver if self.field is not None else None

        if resolver is None:
            return _find_field_source(self.cls, self.field_name)

        function = resolver.wrapped_func

        # e.g. the function of a `@staticmethod`
        if isinstance(function, (staticmethod, classmethod)):
            function = function.__func__

        return SourceFinder().find_function_from_object(function)


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


class UnsupportedInheritedFieldError(StrawberryException):
    def __init__(
        self,
        field_name: str,
        cls: type,
        base: type,
        *,
        reason: Literal["default_factory", "resolver"],
    ) -> None:
        self.cls = base
        self.field_name = field_name

        if reason == "default_factory":
            template = (
                "Pydantic input `{cls}` can't use the default factory of field "
                "`{field}`, inherited from `{base}`"
            )
            self.annotation_message = "default factory that pydantic doesn't see"
            self.suggestion = (
                "Strawberry types are dataclasses, which don't keep a field's default "
                "factory on the class, so pydantic doesn't see it and the field would "
                "be required. Declare the field on the pydantic model instead, e.g. "
                f"`{field_name}: list[str] | None = "
                "pydantic.Field(default_factory=list)`."
            )
        else:
            template = (
                "Pydantic type `{cls}` can't inherit field `{field}` from `{base}`, "
                "as it has a resolver"
            )
            self.annotation_message = "field with a resolver that pydantic sees as data"
            self.suggestion = (
                "Pydantic would make it a field of the model, with the resolver as its "
                "default value. Declare the field as a method with `@strawberry.field` "
                "instead, which Pydantic doesn't see, for example: "
                f"`@strawberry.field def {field_name}(self) -> ...`."
            )

        self.message, self.rich_message = _format_message(
            template, field=field_name, cls=cls.__name__, base=base.__name__
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        source_finder = SourceFinder()

        return source_finder.find_class_attribute_from_object(self.cls, self.field_name)


class UnsupportedFieldOverrideError(StrawberryException):
    def __init__(
        self,
        field_name: str,
        cls: type,
        *,
        overridden: Literal["model_field", "resolver_field", "computed_field"],
    ) -> None:
        self.cls = cls
        self.field_name = field_name

        if overridden == "model_field":
            template = (
                "The resolver of `{field}` on pydantic model `{cls}` overrides a "
                "model field with the same name"
            )
            self.annotation_message = "resolver with the name of a model field"
            self.suggestion = (
                "Pydantic would use the resolver as the default value of the field. "
                "Rename the resolver, or remove the model field."
            )
        elif overridden == "resolver_field":
            template = (
                "`{field}` on `{cls}` overrides an inherited field with a resolver, "
                "but isn't a field itself"
            )
            self.annotation_message = "attribute overriding a field with a resolver"
            self.suggestion = (
                "The field would be removed from the GraphQL type. To change its "
                "resolver, decorate the method with `@strawberry.pydantic.field`, or "
                "rename the method to keep the inherited field."
            )
        else:
            template = (
                "`{field}` on `{cls}` overrides an inherited computed field, but "
                "isn't a field itself"
            )
            self.annotation_message = "attribute overriding a computed field"
            self.suggestion = (
                "Pydantic keeps the computed field, with the method as its value. To "
                "change the field, make the method a computed field with "
                "`@computed_field` and `@property`, or a field with a resolver with "
                "`@strawberry.pydantic.field`. Otherwise rename the method."
            )

        self.message, self.rich_message = _format_message(
            template, field=field_name, cls=cls.__name__
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        return SourceFinder().find_class_attribute_from_object(
            self.cls, self.field_name
        )


class StrawberryBaseBeforeModelError(StrawberryException):
    def __init__(self, cls: type, base: type, decorator: str) -> None:
        self.cls = cls

        definition = base.__strawberry_definition__  # type: ignore[attr-defined]
        kind = (
            "input"
            if definition.is_input
            else "interface"
            if definition.is_interface
            else "type"
        )
        bases = vars(cls).get("__orig_bases__", cls.__bases__)
        reordered = ", ".join(
            _format_base(base)
            for base in sorted(
                bases,
                # the models first, keeping the order of the other bases
                key=lambda base: (
                    not (isinstance(base, type) and issubclass(base, BaseModel))
                ),
            )
        )

        self.message = (
            f"Pydantic {decorator} `{cls.__name__}` extends the Strawberry {kind} "
            f"`{base.__name__}` before a Pydantic model"
        )
        self.rich_message = (
            f"Pydantic {decorator} `[underline]{cls.__name__}[/]` extends the "
            f"Strawberry {kind} `[underline]{base.__name__}[/]` before a Pydantic "
            "model"
        )
        self.annotation_message = "Strawberry base before the Pydantic model"
        self.suggestion = _escape_markup(
            f"The `__init__` of `{base.__name__}` would replace Pydantic's, so the "
            "model couldn't be created. List the Pydantic models first: "
            f"`class {cls.__name__}({reordered})`."
        )

        super().__init__(self.message)

    @cached_property
    def exception_source(self) -> ExceptionSource | None:
        return SourceFinder().find_class_from_object(self.cls)


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
            bases = vars(cls).get("__orig_bases__", cls.__bases__)
            shared_bases = [base for base in bases if _is_undecorated_model(base)]

            if shared_bases:
                # the model already shares its fields with an undecorated base
                # model, which the input can extend too
                shared = ", ".join(_format_base(base) for base in shared_bases)
                noun, pronoun = (
                    ("base model", "it")
                    if len(shared_bases) == 1
                    else ("base models", "them")
                )

                self.suggestion = _escape_markup(
                    f"Inputs can't implement interfaces, so `{name}` can't be "
                    f"subclassed for an input. Extend its undecorated {noun} "
                    f"instead, and move any other fields to share to {pronoun}, "
                    f"for example: `@strawberry.pydantic.input class "
                    f"{name}Input({shared})`."
                )
            else:
                new_bases = ", ".join(
                    [
                        f"{name}Base",
                        *(
                            _format_base(base)
                            for base in bases
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
                    f"`@strawberry.pydantic.{current_decorator} "
                    f"class {name}({new_bases})` "
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
