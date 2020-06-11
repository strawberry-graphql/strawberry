import dataclasses
from typing import Callable, List, Optional, Type, cast

from strawberry.exceptions import MissingReturnAnnotationError

from .arguments import get_arguments_from_resolver
from .permission import BasePermission
from .types.types import FederationFieldParams, FieldDefinition
from .utils.str_converters import to_camel_case


def check_return_annotation(field_definition: FieldDefinition):
    f = cast(Callable, field_definition.base_resolver)
    name = cast(str, field_definition.name)

    if "return" not in f.__annotations__:
        raise MissingReturnAnnotationError(name)


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

    def __setattr__(self, name, value):
        if name == "type":
            self._field_definition.type = value

        if value and name == "name":
            if not self._field_definition.origin_name:
                self._field_definition.origin_name = value

            if not self._field_definition.name:
                self._field_definition.name = to_camel_case(value)

        return super().__setattr__(name, value)

    def __call__(self, f):
        f._field_definition = self._field_definition
        f._field_definition.name = f._field_definition.name or to_camel_case(f.__name__)
        f._field_definition.base_resolver = f
        f._field_definition.origin = f
        f._field_definition.arguments = get_arguments_from_resolver(
            f, f._field_definition.name
        )

        check_return_annotation(f._field_definition)

        f._field_definition.type = f.__annotations__["return"]

        return f


def field(
    f=None,
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    resolver: Optional[Callable] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    federation: Optional[FederationFieldParams] = None
):
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

    origin_name = f.__name__ if f else None
    name = name or (to_camel_case(origin_name) if origin_name else None)

    wrap = StrawberryField(
        field_definition=FieldDefinition(
            origin_name=origin_name,
            name=name,
            type=None,  # type: ignore
            origin=f,  # type: ignore
            description=description,
            base_resolver=resolver,
            is_subscription=is_subscription,
            permission_classes=permission_classes or [],
            arguments=(
                get_arguments_from_resolver(resolver, origin_name) if resolver else []
            ),
            federation=federation or FederationFieldParams(),
        )
    )

    if f:
        return wrap(f)

    return wrap
