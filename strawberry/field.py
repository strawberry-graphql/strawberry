import dataclasses
from typing import Any, Callable, List, Optional, Type, Union

from .permission import BasePermission
from .types.fields.resolver import StrawberryResolver
from .types.types import FederationFieldParams, FieldDefinition, ArgumentDefinition
from .utils.str_converters import to_camel_case


_RESOLVER_TYPE = Union[StrawberryResolver, Callable]


class StrawberryField(dataclasses.Field):
    _field_definition: FieldDefinition

    def __init__(self, field_definition: FieldDefinition):
        super().__init__(  # type: ignore
            default=dataclasses.MISSING,
            default_factory=dataclasses.MISSING,
            init=field_definition.base_resolver is None,
            repr=True,
            hash=None,
            compare=True,
            metadata=None,
        )

        self._field_definition = field_definition
        self._graphql_name = field_definition.name

        self.name = field_definition.origin_name
        if field_definition.type is not None:
            self.type = field_definition.type

        self.description: Optional[str] = field_definition.description
        self.origin: Optional[Union[Type, Callable]] = field_definition.origin
        self.base_resolver: Optional[StrawberryResolver] = field_definition.base_resolver

        self.child = field_definition.child

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
    def default_value(self) -> Any:
        return self._field_definition.default_value

    @property
    def deprecation_reason(self) -> Optional[str]:
        return self._field_definition.deprecation_reason

    @property
    def federation(self) -> FederationFieldParams:
        return self._field_definition.federation

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
    def is_child_optional(self) -> bool:
        return self._field_definition.is_child_optional

    @property
    def is_list(self) -> bool:
        return self._field_definition.is_list

    @property
    def is_optional(self) -> bool:
        return self._field_definition.is_optional

    @property
    def is_subscription(self) -> bool:
        return self._field_definition.is_subscription

    @property
    def is_union(self) -> bool:
        return self._field_definition.is_union

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
    def permission_classes(self) -> List[Type[BasePermission]]:
        return self._field_definition.permission_classes

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

    field_definition = FieldDefinition(
        origin_name=None,  # modified by resolver in __call__
        name=name,
        type=None,
        description=description,
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        federation=federation or FederationFieldParams(),
        deprecation_reason=deprecation_reason,
    )

    field_ = StrawberryField(field_definition)

    if resolver:
        return field_(resolver)
    return field_


__all__ = ["FederationFieldParams", "FieldDefinition", "StrawberryField", "field"]
