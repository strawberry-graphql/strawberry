import dataclasses
from typing import Any, Callable, List, Optional, Type, Union

from .permission import BasePermission
from .types.fields.resolver import StrawberryResolver
from .types.types import FederationFieldParams, ArgumentDefinition, undefined
from .union import StrawberryUnion
from .utils.str_converters import to_camel_case

_RESOLVER_TYPE = Union[StrawberryResolver, Callable]


class StrawberryField(dataclasses.Field):

    def __init__(
            self,
            name: Optional[str],
            origin_name: Optional[str],
            type_: Optional[Union[Type, StrawberryUnion]],
            origin: Optional[Union[Type, Callable]] = None,
            child: Optional["StrawberryField"] = None,
            is_subscription: bool = False,
            is_optional: bool = False,
            is_child_optional: bool = False,
            is_list: bool = False,
            is_union: bool = False,
            federation: FederationFieldParams = FederationFieldParams(),
            description: Optional[str] = None,
            base_resolver: Optional["StrawberryResolver"] = None,
            permission_classes: List[Type[BasePermission]] = (),
            default_value: Any = undefined,
            deprecation_reason: Optional[str] = None,
    ):

        super().__init__(  # type: ignore
            default=dataclasses.MISSING,
            default_factory=dataclasses.MISSING,
            init=base_resolver is None,
            repr=True,
            hash=None,
            compare=True,
            metadata=None,
        )

        self._graphql_name = name
        self.name = origin_name
        if type_ is not None:
            self.type = type_

        self.description: Optional[str] = description
        self.origin: Optional[Union[Type, Callable]] = origin
        self.base_resolver: Optional[StrawberryResolver] = base_resolver

        self.default_value = default_value

        self.child = child
        self.is_child_optional = is_child_optional

        self.is_list = is_list
        self.is_optional = is_optional
        self.is_subscription = is_subscription
        self.is_union = is_union

        self.federation: FederationFieldParams = federation
        self.permission_classes: List[Type[BasePermission]] = list(permission_classes)

        self.deprecation_reason = deprecation_reason

    def __call__(self, resolver: _RESOLVER_TYPE) -> "StrawberryField":
        """Add a resolver to the field"""

        # Allow for StrawberryResolvers or bare functions to be provided
        if not isinstance(resolver, StrawberryResolver):
            resolver = StrawberryResolver(resolver)

        self.origin = resolver.wrapped_func
        self.base_resolver = resolver
        self.type = resolver.type

        # Don't add field to __init__ or __repr__
        self.init = False
        self.repr = False

        # TODO: We have tests for exceptions at field creation, but using
        #       properties defers them
        _ = resolver.arguments

        return self

    @property
    def arguments(self) -> List[ArgumentDefinition]:
        if not self.base_resolver:
            # TODO: Should this return None if no resolver?
            return []

        return self.base_resolver.arguments

    @property
    def graphql_name(self) -> Optional[str]:
        if self._graphql_name:
            return to_camel_case(self._graphql_name)
        if self.name:
            return to_camel_case(self.name)
        if self.resolver_name:
            return to_camel_case(self.resolver_name)
        return None

    @property
    def python_name(self) -> Optional[str]:
        # TODO: Remove
        return self.name

    @property
    def resolver_name(self) -> Optional[str]:
        if self.base_resolver:
            return self.base_resolver.name
        else:
            return None

    @property
    def type(self) -> Any:
        return self._type

    @type.setter
    def type(self, type_: Any) -> None:
        self._type = type_


def field(
        resolver: Optional[_RESOLVER_TYPE] = None,
        *,
        name: Optional[str] = None,
        is_subscription: bool = False,
        description: Optional[str] = None,
        permission_classes: Optional[List[Type[BasePermission]]] = None,
        federation: Optional[FederationFieldParams] = None,
        deprecation_reason: Optional[str] = None,
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

    field_ = StrawberryField(
        origin_name=None,  # modified by resolver in __call__
        name=name,
        type_=None,
        description=description,
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        federation=federation or FederationFieldParams(),
        deprecation_reason=deprecation_reason,
    )

    if resolver:
        return field_(resolver)
    return field_


__all__ = ["FederationFieldParams", "StrawberryField", "field"]
