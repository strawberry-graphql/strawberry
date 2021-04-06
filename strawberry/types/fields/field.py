from __future__ import annotations

from typing import Callable, Optional, TypeVar, Union, Generic, List, Type

from strawberry.types import StrawberryArgument, StrawberryResolver, StrawberryType

T = TypeVar("T")
S = TypeVar("S")
_RESOLVER_TYPE = Union[StrawberryResolver[S], Callable[..., S]]


class StrawberryField(Generic[T]):
    """Strawberry field

    >>> StrawberryField(
    ...     type_=int,
    ...     resolver=lambda: 5,
    ...     name="cool_field"
    ... )
    """

    class _NO_DEFAULT_VALUE:
        """Sentinel value to indicate that a field has no default.

        `None` is not a good option because it can actually be the default for a
        nullable type.
        """

    class _NO_FIELD_TYPE:
        """Sentinel value to indicate a field has not received a type"""

    def __init__(
        self, *,
        type_: Optional[Union[Type[T], StrawberryType[T]]] = _NO_FIELD_TYPE,
        resolver: Optional[_RESOLVER_TYPE[T]] = None,
        name: Optional[str] = None,
        default_value: Optional[T] = _NO_DEFAULT_VALUE,
        description: Optional[str] = None,
        permission_classes: Optional[object] = None,
    ):

        # TODO: Move this check to someplace better
        if (type_ and resolver) and (type_ != resolver.type):
            # TODO: Raise Strawberry exception
            ...

        self._resolver: Optional[_RESOLVER_TYPE[T]] = None
        self.resolver = resolver

        self._type = None
        self.type = type_

        self._graphql_name = name
        self.description = description
        # TODO: Deal with permissions
        self.permission_classes = permission_classes
        # TODO: Maybe just use a lambda that returns static value as resolver instead
        self.default_value = default_value

    def __call__(self, resolver: _RESOLVER_TYPE[T]) -> StrawberryField[T]:
        """Add a resolver to the field"""
        self.resolver = resolver
        return self

    @property
    def arguments(self) -> List[StrawberryArgument]:
        if not self.resolver:
            return []

        return self.resolver.arguments

    @property
    def graphql_name(self) -> Optional[str]:
        """The name specified explicitly, or if not set the wrapped resolver's
        name
        """
        if self._graphql_name:
            return self._graphql_name
        if self.resolver:
            return self.resolver.name

        # TODO: Should we raise an exception instead?
        return None

    @property
    def resolver(self) -> Optional[_RESOLVER_TYPE[T]]:
        return self._resolver

    @resolver.setter
    def resolver(self, resolver: _RESOLVER_TYPE[T]) -> None:
        # Allow for StrawberryResolvers or bare functions to be provided
        if not isinstance(resolver, StrawberryResolver):
            resolver = StrawberryResolver(resolver)

        self.resolver = resolver

    @property
    def type(self) -> Optional[StrawberryType[T]]:
        if self._type is not None:
            return self._type
        if self.resolver is not None:
            return self.resolver.type

        # TODO: Should we raise an exception instead?
        return None

    @type.setter
    def type(self, type_: Union[Type[T], StrawberryType[T]]) -> None:
        if not isinstance(type_, StrawberryType):
            type_ = StrawberryType(type_)

        self._type = type_


def field(
    resolver: Optional[_RESOLVER_TYPE[T]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    permission_classes: Optional[object] = None,  # TODO
) -> StrawberryField:
    """Annotates a method or property as a GraphQL field.

    This is normally used inside a type declaration:

    >>> @strawberry.type:
    >>> class X:
    >>>     field_abc: str = strawberry.field(description="ABC")

    >>>     @strawberry.field(description="ABC")
    >>>     def field_with_resolver(self, info) -> str:
    >>>         return "abc"

    it can be used both as decorator and as a normal function.
    """

    return StrawberryField(
        resolver=resolver,
        name=name,
        description=description,
        permission_classes=permission_classes,
    )
