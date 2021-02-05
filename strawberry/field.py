import dataclasses
from typing import Callable, List, Optional, Type, Union

from .permission import BasePermission
from .types.fields.resolver import StrawberryResolver
from .types.types import FederationFieldParams, FieldDefinition
from .utils.str_converters import to_camel_case


_RESOLVER_TYPE = Union[StrawberryResolver, Callable]


class StrawberryField(dataclasses.Field):
    _field_definition: FieldDefinition

    def __init__(self, field_definition: FieldDefinition):
        self._field_definition = field_definition

        super().__init__(  # type: ignore
            default=dataclasses.MISSING,
            default_factory=dataclasses.MISSING,
            init=field_definition.base_resolver is None,
            repr=True,
            hash=None,
            compare=True,
            metadata=None,
        )

    def __call__(self, resolver: _RESOLVER_TYPE) -> "StrawberryField":
        """Add a resolver to the field"""

        # Allow for StrawberryResolvers or bare functions to be provided
        if not isinstance(resolver, StrawberryResolver):
            resolver = StrawberryResolver(resolver)

        self._field_definition.origin_name = resolver.name
        self._field_definition.origin = resolver.wrapped_func
        self._field_definition.base_resolver = resolver
        self._field_definition.arguments = resolver.arguments
        self._field_definition.type = resolver.type

        # Don't add field to __init__ or __repr__
        self.init = False
        self.repr = False

        return self

    def __setattr__(self, name, value):
        if name == "type":
            self._field_definition.type = value

        if value and name == "name":
            if not self._field_definition.origin_name:
                self._field_definition.origin_name = value

            if not self._field_definition.name:
                self._field_definition.name = to_camel_case(value)

        return super().__setattr__(name, value)


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
        arguments=[],  # modified by resolver in __call__
        federation=federation or FederationFieldParams(),
        deprecation_reason=deprecation_reason,
    )

    field_ = StrawberryField(field_definition)

    if resolver:
        return field_(resolver)
    return field_


__all__ = ["FederationFieldParams", "FieldDefinition", "StrawberryField", "field"]
