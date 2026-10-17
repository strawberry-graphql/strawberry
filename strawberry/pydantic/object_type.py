"""Object type decorators for Pydantic models in Strawberry GraphQL.

This module provides decorators to convert Pydantic BaseModel classes directly
into GraphQL types, inputs, and interfaces without requiring a separate wrapper class.
"""

from __future__ import annotations

import builtins
import dataclasses
import functools
from typing import TYPE_CHECKING, TypeVar, overload

from pydantic import BaseModel

from strawberry.exceptions import InvalidSuperclassInterfaceError
from strawberry.schema_directives import OneOf
from strawberry.types.base import StrawberryObjectDefinition
from strawberry.types.object_type import _get_interfaces
from strawberry.utils.str_converters import to_camel_case

from .conversion import build_pydantic_model, dump_pydantic_model
from .exceptions import (
    ModelAlreadyDecoratedError,
    NotAPydanticModelError,
    StrawberryBaseBeforeModelError,
)
from .fields import (
    check_serializers,
    get_pydantic_fields,
    get_resolver_fields,
    get_type_var_map,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


def _find_strawberry_base_before_model(
    cls: builtins.type[BaseModel],
) -> builtins.type | None:
    """Return a regular Strawberry type that comes before the Pydantic models.

    For example `Node` in `class Product(Node, BaseModel)`. Its dataclass
    `__init__` comes before Pydantic's in the MRO, so the model can't be created.
    """
    for base in cls.__mro__[1:]:
        if issubclass(base, BaseModel):
            return None

        # only the class's own definition, not one inherited from its bases
        if "__strawberry_definition__" in vars(base):
            return base

    return None


@dataclasses.dataclass(eq=False)
class _GenericModelDefinition(StrawberryObjectDefinition):
    """The definition of a generic model, like `Page` in `Page[User]`.

    Pydantic parametrizes generic models with subclasses, which would inherit
    this definition. Instead, reading it from a parametrization that has no type
    parameters left, like `Page[User]`, gives the parametrization a definition
    of its own, specialized like `Page[User]` is with a generic
    `@strawberry.type`, which names it `UserPage`. Pydantic reuses the classes of
    its parametrizations, so each one is only built once.
    """

    # the option of the decorator that isn't part of the definition
    include_computed: bool = True

    def __get__(
        self, instance: object, owner: builtins.type[BaseModel]
    ) -> StrawberryObjectDefinition:
        metadata = owner.__pydantic_generic_metadata__

        # e.g. the generic model itself, a subclass of it, or `Page[T]`
        if metadata["origin"] is not self.origin or metadata["parameters"]:
            return self

        try:
            _process_pydantic_type(
                owner,
                name=self.name,
                is_input=self.is_input,
                is_interface=self.is_interface,
                description=self.description,
                directives=self.directives,
                include_computed=self.include_computed,
                generic=self,
            )
        except AttributeError as error:
            # Otherwise hasattr() would hide a construction failure and make
            # the parametrized model look undecorated.
            raise RuntimeError(
                f"Couldn't build the definition of `{owner.__name__}`: {error}"
            ) from error

        return vars(owner)["__strawberry_definition__"]


# The decorators return the class they're given, so type checkers keep the
# model's own type instead of a plain BaseModel
ModelT = TypeVar("ModelT", bound="BaseModel")


def _process_pydantic_type(
    cls: builtins.type[ModelT],
    *,
    name: str | None = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
    generic: _GenericModelDefinition | None = None,
) -> builtins.type[ModelT]:
    """Process a Pydantic BaseModel class and add GraphQL metadata.

    Args:
        cls: The Pydantic BaseModel class to process
        name: The GraphQL type name (defaults to class name)
        is_input: Whether this is an input type
        is_interface: Whether this is an interface type
        description: The GraphQL type description
        directives: GraphQL directives to apply
        include_computed: Whether to include computed fields
        generic: The definition of the generic model `cls` parametrizes, when
            it's specialized, like `Page[User]`

    Returns:
        The processed BaseModel class with GraphQL metadata
    """
    decorator = "input" if is_input else "interface" if is_interface else "type"

    if not (isinstance(cls, builtins.type) and issubclass(cls, BaseModel)):
        raise NotAPydanticModelError(cls, decorator)

    generic_metadata = cls.__pydantic_generic_metadata__

    # before the check for decorated models, as they can already be specialized
    if generic is None and (origin := generic_metadata["origin"]) is not None:
        raise TypeError(
            f"`{cls.__name__}` is a parametrized generic model, which can't be "
            f"decorated: decorate `{origin.__name__}` instead, which makes "
            f"`{cls.__name__}` a GraphQL type too, or a subclass of `{cls.__name__}` "
            "to give it a name of its own"
        )

    if "__strawberry_definition__" in vars(cls):
        raise ModelAlreadyDecoratedError(cls, decorator)

    if (base := _find_strawberry_base_before_model(cls)) is not None:
        raise StrawberryBaseBeforeModelError(cls, base=base, decorator=decorator)

    name = name or to_camel_case(cls.__name__)

    resolver_fields = get_resolver_fields(
        cls, is_input=is_input, include_computed=include_computed
    )

    fields = [
        *get_pydantic_fields(
            cls=cls,
            is_input=is_input,
            include_computed=include_computed,
            # e.g. a computed field overridden by a resolver field in a subclass
            resolver_field_names={field.python_name for field in resolver_fields},
        ),
        *resolver_fields,
    ]

    if not is_input:
        check_serializers(
            cls,
            field_names=[field.python_name for field in fields if field.python_name],
            decorator=decorator,
        )

    interfaces = _get_interfaces(cls)

    if is_input and interfaces:
        raise InvalidSuperclassInterfaceError(
            cls=cls, input_name=name, interfaces=interfaces
        )

    # types implement the specialized interfaces, as generic ones can't be part
    # of the schema
    interfaces = [
        interface
        for interface in interfaces
        if not isinstance(interface, _GenericModelDefinition)
    ]

    # generic models specialize their parametrizations
    definition_type = (
        functools.partial(
            _GenericModelDefinition,
            include_computed=include_computed,
        )
        if generic_metadata["parameters"]
        else StrawberryObjectDefinition
    )

    cls.__strawberry_definition__ = definition_type(  # type: ignore
        name=name,
        is_input=is_input,
        is_interface=is_interface,
        interfaces=interfaces,
        description=description,
        directives=directives,
        origin=cls,
        extend=False,
        fields=fields,
        # like `@strawberry.type`, resolvers can return objects that aren't
        # instances of the model, e.g. ORM rows, unless it defines `is_type_of`
        is_type_of=getattr(cls, "is_type_of", None),
        resolve_type=getattr(cls, "resolve_type", None),
        from_input=build_pydantic_model if is_input else None,
        to_input=dump_pydantic_model if is_input else None,
        # named like the specialized types of generic Strawberry types, e.g.
        # `UserPage` for `Page[User]`, by the schema's name converter
        concrete_of=generic,
        type_var_map=get_type_var_map(cls) if generic is not None else {},
    )

    return cls


@overload
def type(
    cls: builtins.type[ModelT],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> builtins.type[ModelT]: ...


@overload
def type(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> Callable[[builtins.type[ModelT]], builtins.type[ModelT]]: ...


def type(
    cls: builtins.type[ModelT] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> builtins.type[ModelT] | Callable[[builtins.type[ModelT]], builtins.type[ModelT]]:
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL type.

    This decorator allows you to use Pydantic models directly as GraphQL types
    without needing to create a separate wrapper class.

    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL type name (defaults to class name)
        description: The GraphQL type description
        directives: GraphQL directives to apply to the type
        include_computed: Whether to include computed fields

    Returns:
        The decorated BaseModel class with GraphQL metadata

    Example:
        @strawberry.pydantic.type
        class User(BaseModel):
            name: str
            age: int

        # All fields from the Pydantic model will be included in the GraphQL type

        # You can also use strawberry.field() for field-level customization:
        @strawberry.pydantic.type
        class User(BaseModel):
            name: str
            age: Annotated[int, strawberry.field(directives=[SomeDirective()])]
    """

    def wrap(cls: builtins.type[ModelT]) -> builtins.type[ModelT]:
        return _process_pydantic_type(
            cls,
            name=name,
            is_input=False,
            is_interface=False,
            description=description,
            directives=directives,
            include_computed=include_computed,
        )

    if cls is None:
        return wrap

    return wrap(cls)


@overload
def input(
    cls: builtins.type[ModelT],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    one_of: bool | None = None,
) -> builtins.type[ModelT]: ...


@overload
def input(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    one_of: bool | None = None,
) -> Callable[[builtins.type[ModelT]], builtins.type[ModelT]]: ...


def input(
    cls: builtins.type[ModelT] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    one_of: bool | None = None,
) -> builtins.type[ModelT] | Callable[[builtins.type[ModelT]], builtins.type[ModelT]]:
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL input type.

    This decorator allows you to use Pydantic models directly as GraphQL input types
    without needing to create a separate wrapper class.

    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL input type name (defaults to class name)
        description: The GraphQL input type description
        directives: GraphQL directives to apply to the input type
        one_of: Whether the input type is a `oneOf` type

    Returns:
        The decorated BaseModel class with GraphQL input metadata

    Example:
        @strawberry.pydantic.input
        class CreateUserInput(BaseModel):
            name: str
            age: int

        # All fields from the Pydantic model will be included in the GraphQL input type
    """
    if one_of:
        directives = (*(directives or ()), OneOf())

    def wrap(cls: builtins.type[ModelT]) -> builtins.type[ModelT]:
        return _process_pydantic_type(
            cls,
            name=name,
            is_input=True,
            is_interface=False,
            description=description,
            directives=directives,
            include_computed=False,  # Input types don't need computed fields
        )

    if cls is None:
        return wrap

    return wrap(cls)


@overload
def interface(
    cls: builtins.type[ModelT],
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> builtins.type[ModelT]: ...


@overload
def interface(
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> Callable[[builtins.type[ModelT]], builtins.type[ModelT]]: ...


def interface(
    cls: builtins.type[ModelT] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Sequence[object] | None = (),
    include_computed: bool = True,
) -> builtins.type[ModelT] | Callable[[builtins.type[ModelT]], builtins.type[ModelT]]:
    """Decorator to convert a Pydantic BaseModel directly into a GraphQL interface.

    This decorator allows you to use Pydantic models directly as GraphQL interfaces
    without needing to create a separate wrapper class.

    Args:
        cls: The Pydantic BaseModel class to convert
        name: The GraphQL interface name (defaults to class name)
        description: The GraphQL interface description
        directives: GraphQL directives to apply to the interface
        include_computed: Whether to include computed fields

    Returns:
        The decorated BaseModel class with GraphQL interface metadata

    Example:
        @strawberry.pydantic.interface
        class Node(BaseModel):
            id: str
    """

    def wrap(cls: builtins.type[ModelT]) -> builtins.type[ModelT]:
        return _process_pydantic_type(
            cls,
            name=name,
            is_input=False,
            is_interface=True,
            description=description,
            directives=directives,
            include_computed=include_computed,
        )

    if cls is None:
        return wrap

    return wrap(cls)


__all__ = ["input", "interface", "type"]
