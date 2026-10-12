"""Fields with a resolver on pydantic types."""

from __future__ import annotations

import copy
import inspect
from functools import partial, wraps
from types import FunctionType
from typing import TYPE_CHECKING, Any, TypeVar, cast, overload

from strawberry.exceptions import MissingReturnAnnotationError
from strawberry.types.field import StrawberryField
from strawberry.types.field import field as strawberry_field

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Mapping, Sequence

    from strawberry.extensions.field_extension import FieldExtension
    from strawberry.permission import BasePermission

ResolverT = TypeVar("ResolverT", bound="Callable[..., Any]")

_FIELD_ATTRIBUTE = "__strawberry_field__"
# marks the decorator returned by `strawberry.pydantic.field(...)`
_DECORATOR_ATTRIBUTE = "__strawberry_pydantic_field__"


@overload
def field(
    resolver: ResolverT,
    *,
    name: str | None = None,
    description: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> ResolverT: ...


@overload
def field(
    *,
    name: str | None = None,
    description: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> Callable[[ResolverT], ResolverT]: ...


def field(
    resolver: ResolverT | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    permission_classes: list[type[BasePermission]] | None = None,
    deprecation_reason: str | None = None,
    metadata: Mapping[Any, Any] | None = None,
    directives: Sequence[object] | None = (),
    extensions: list[FieldExtension] | None = None,
    graphql_type: Any | None = None,
) -> ResolverT | Callable[[ResolverT], ResolverT]:
    """Add a field with a resolver to a `strawberry.pydantic` type.

    It takes the field options of `strawberry.field`. Pydantic doesn't allow
    `strawberry.field` in a model, so this decorator returns a method wrapper,
    and `strawberry.pydantic.type` adds the field to the GraphQL type:

    ```python
    @strawberry.pydantic.type
    class User(BaseModel):
        id: strawberry.ID

        @strawberry.pydantic.field
        async def posts(self, info: strawberry.Info) -> list[Post]:
            return await info.context.loaders.posts.load(self.id)
    ```
    """

    def wrap(resolver: ResolverT) -> ResolverT:
        # Each decoration owns its metadata without mutating the shared resolver.
        resolver = _wrap_resolver(resolver)

        resolver_field = strawberry_field(
            resolver,
            name=name,
            description=description,
            permission_classes=permission_classes,
            deprecation_reason=deprecation_reason,
            metadata=metadata,
            directives=directives,
            extensions=extensions,
            graphql_type=graphql_type,
        )

        assert resolver_field.base_resolver is not None

        if (
            graphql_type is None
            and resolver_field.base_resolver.type_annotation is None
        ):
            raise MissingReturnAnnotationError(
                resolver_field.base_resolver.name,
                resolver=resolver_field.base_resolver,
            )

        setattr(resolver, _FIELD_ATTRIBUTE, resolver_field)

        return resolver

    if resolver is None:
        setattr(wrap, _DECORATOR_ATTRIBUTE, True)

        return wrap

    return wrap(resolver)


def _wrap_resolver(resolver: ResolverT) -> ResolverT:
    if isinstance(resolver, (staticmethod, classmethod)):
        return cast("ResolverT", type(resolver)(_wrap_resolver(resolver.__func__)))

    # inspect recognizes async functions and partials, but not callable objects.
    async_target: Callable[..., Any] = resolver
    while isinstance(async_target, partial):
        async_target = async_target.func
    if not inspect.isroutine(async_target):
        async_target = async_target.__call__  # type: ignore[operator]

    wrapper: Callable[..., Any]
    if inspect.isasyncgenfunction(async_target):

        @wraps(resolver)
        async def async_generator(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            async for item in resolver(*args, **kwargs):
                yield item

        wrapper = async_generator
    elif inspect.iscoroutinefunction(async_target):

        @wraps(resolver)
        async def asynchronous(*args: Any, **kwargs: Any) -> Any:
            return await resolver(*args, **kwargs)

        wrapper = asynchronous
    else:

        @wraps(resolver)
        def synchronous(*args: Any, **kwargs: Any) -> Any:
            return resolver(*args, **kwargs)

        wrapper = synchronous

    # A function wrapper would otherwise inject the model as `self` into an
    # already-bound method, a partial, or a callable instance.
    if inspect.ismethod(resolver) or not hasattr(type(resolver), "__get__"):
        return cast("ResolverT", staticmethod(wrapper))

    return cast("ResolverT", wrapper)


def is_field_decorator(value: object) -> bool:
    """Return whether `value` is `strawberry.pydantic.field` without a resolver.

    That's `strawberry.pydantic.field` itself, or what it returns when it's
    called with options only, e.g. when it's used on a model field.
    """
    return value is field or (
        isinstance(value, FunctionType)
        and getattr(value, _DECORATOR_ATTRIBUTE, False) is True
    )


def _get_marked_field(value: object) -> StrawberryField | None:
    # only look at what can be a method, other objects may not like getattr
    if not (
        isinstance(value, (FunctionType, staticmethod, classmethod))
        or type(value).__module__ == "functools"
    ):
        return None

    marked_field = getattr(value, _FIELD_ATTRIBUTE, None)

    # `@staticmethod` or `@classmethod` applied on top of the marker
    if marked_field is None and isinstance(value, (staticmethod, classmethod)):
        marked_field = getattr(value.__func__, _FIELD_ATTRIBUTE, None)

    return marked_field if isinstance(marked_field, StrawberryField) else None


def get_resolver_field(value: object) -> StrawberryField | None:
    """Return the field of a class attribute marked with `strawberry.pydantic.field`."""
    marked_field = _get_marked_field(value)

    if marked_field is None:
        return None

    assert marked_field.base_resolver is not None

    # decorators applied on top of the marker, like `functools.cache` or
    # `staticmethod`, must be part of the resolver
    if marked_field.base_resolver.wrapped_func is not value:
        return copy.copy(marked_field)(value)  # type: ignore[arg-type]

    return marked_field
