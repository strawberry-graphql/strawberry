from __future__ import annotations

import builtins
import dataclasses
import inspect
import sys
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from cached_property import cached_property  # type: ignore
from typing_extensions import Literal

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import UNSET, StrawberryArgument
from strawberry.exceptions import (
    FieldWithResolverAndDefaultFactoryError,
    FieldWithResolverAndDefaultValueError,
    InvalidFieldArgument,
    PrivateStrawberryFieldError,
)
from strawberry.private import Private
from strawberry.type import StrawberryType
from strawberry.types.info import Info
from strawberry.union import StrawberryUnion
from strawberry.utils.mixins import GraphQLNameMixin

from .permission import BasePermission
from .types.resolver import StrawberryResolver
from .types.types import FederationFieldParams, TypeDefinition


_RESOLVER_TYPE = Union[StrawberryResolver, Callable]


class StrawberryField(dataclasses.Field, GraphQLNameMixin):
    python_name: str

    def __init__(
        self,
        python_name: Optional[str] = None,
        graphql_name: Optional[str] = None,
        type_annotation: Optional[StrawberryAnnotation] = None,
        origin: Optional[Union[Type, Callable]] = None,
        is_subscription: bool = False,
        federation: FederationFieldParams = None,
        description: Optional[str] = None,
        base_resolver: Optional[StrawberryResolver] = None,
        permission_classes: List[Type[BasePermission]] = (),  # type: ignore
        default: object = UNSET,
        default_factory: Union[Callable[[], Any], object] = UNSET,
        deprecation_reason: Optional[str] = None,
    ):
        federation = federation or FederationFieldParams()

        # basic fields are fields with no provided resolver
        is_basic_field = not base_resolver

        super().__init__(  # type: ignore
            default=(default if default is not UNSET else dataclasses.MISSING),
            default_factory=(
                # mypy is not able to understand that default factory
                # is a callable so we do a type ignore
                default_factory  # type: ignore
                if default_factory is not UNSET
                else dataclasses.MISSING
            ),
            init=is_basic_field,
            repr=is_basic_field,
            compare=is_basic_field,
            hash=None,
            metadata={},
        )

        self.graphql_name = graphql_name
        if python_name is not None:
            self.python_name = python_name

        self.type_annotation = type_annotation

        self.description: Optional[str] = description
        self.origin: Optional[Union[Type, Callable]] = origin

        self._base_resolver: Optional[StrawberryResolver] = None
        if base_resolver is not None:
            self.base_resolver = base_resolver

        # Note: StrawberryField.default is the same as
        # StrawberryField.default_value except that `.default` uses
        # `dataclasses.MISSING` to represent an "undefined" value and
        # `.default_value` uses `UNSET`
        self.default_value = default

        self.is_subscription = is_subscription

        self.federation: FederationFieldParams = federation
        self.permission_classes: List[Type[BasePermission]] = list(permission_classes)

        self.deprecation_reason = deprecation_reason

    def __call__(self, resolver: _RESOLVER_TYPE) -> "StrawberryField":
        """Add a resolver to the field"""

        # Allow for StrawberryResolvers or bare functions to be provided
        if not isinstance(resolver, StrawberryResolver):
            resolver = StrawberryResolver(resolver)

        for argument in resolver.arguments:
            if isinstance(argument.type_annotation.annotation, str):
                continue
            elif isinstance(argument.type, StrawberryUnion):
                raise InvalidFieldArgument(
                    self.python_name,
                    argument.python_name,
                    "Union",
                )
            elif getattr(argument.type, "_type_definition", False):
                if argument.type._type_definition.is_interface:
                    raise InvalidFieldArgument(
                        self.python_name,
                        argument.python_name,
                        "Interface",
                    )

        self.base_resolver = resolver

        return self

    @property
    def arguments(self) -> List[StrawberryArgument]:
        if not self.base_resolver:
            return []

        return self.base_resolver.arguments

    def _python_name(self) -> Optional[str]:
        if self.name:
            return self.name

        if self.base_resolver:
            return self.base_resolver.name

        return None

    def _set_python_name(self, name: str) -> None:
        self.name = name

    # using the function syntax for property here in order to make it easier
    # to ignore this mypy error:
    # https://github.com/python/mypy/issues/4125
    python_name = property(_python_name, _set_python_name)  # type: ignore

    @property
    def base_resolver(self) -> Optional[StrawberryResolver]:
        return self._base_resolver

    @base_resolver.setter
    def base_resolver(self, resolver: StrawberryResolver) -> None:
        self._base_resolver = resolver
        self.origin = resolver.wrapped_func

        # Don't add field to __init__, __repr__ and __eq__ once it has a resolver
        self.init = False
        self.compare = False
        self.repr = False

        # TODO: See test_resolvers.test_raises_error_when_argument_annotation_missing
        #       (https://github.com/strawberry-graphql/strawberry/blob/8e102d3/tests/types/test_resolvers.py#L89-L98)
        #
        #       Currently we expect the exception to be thrown when the StrawberryField
        #       is constructed, but this only happens if we explicitly retrieve the
        #       arguments.
        #
        #       If we want to change when the exception is thrown, this line can be
        #       removed.
        _ = resolver.arguments

    @property  # type: ignore
    def type(self) -> Union[StrawberryType, type]:  # type: ignore
        # We are catching NameError because dataclasses tries to fetch the type
        # of the field from the class before the class is fully defined.
        # This triggers a NameError error when using forward references because
        # our `type` property tries to find the field type from the global namespace
        # but it is not yet defined.
        try:
            if self.base_resolver is not None:
                # Handle unannotated functions (such as lambdas)
                if self.base_resolver.type is not None:
                    return self.base_resolver.type

            assert self.type_annotation is not None

            if not isinstance(self.type_annotation, StrawberryAnnotation):
                # TODO: This is because of dataclasses
                return self.type_annotation

            return self.type_annotation.resolve()
        except NameError:
            return None  # type: ignore

    @type.setter
    def type(self, type_: Any) -> None:
        self.type_annotation = type_

    # TODO: add this to arguments (and/or move it to StrawberryType)
    @property
    def type_params(self) -> List[TypeVar]:
        if hasattr(self.type, "_type_definition"):
            parameters = getattr(self.type, "__parameters__", None)

            return list(parameters) if parameters else []

        # TODO: Consider making leaf types always StrawberryTypes, maybe a
        #       StrawberryBaseType or something
        if isinstance(self.type, StrawberryType):
            return self.type.type_params
        return []

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, builtins.type]]
    ) -> "StrawberryField":
        new_type: Union[StrawberryType, type]

        # TODO: Remove with creation of StrawberryObject. Will act same as other
        #       StrawberryTypes
        if hasattr(self.type, "_type_definition"):
            type_definition: TypeDefinition = self.type._type_definition  # type: ignore

            if type_definition.is_generic:
                type_ = type_definition
                new_type = type_.copy_with(type_var_map)
        else:
            assert isinstance(self.type, StrawberryType)

            new_type = self.type.copy_with(type_var_map)

        new_resolver = (
            self.base_resolver.copy_with(type_var_map)
            if self.base_resolver is not None
            else None
        )

        return StrawberryField(
            python_name=self.python_name,
            graphql_name=self.graphql_name,
            # TODO: do we need to wrap this in `StrawberryAnnotation`?
            # see comment related to dataclasses above
            type_annotation=StrawberryAnnotation(new_type),
            origin=self.origin,
            is_subscription=self.is_subscription,
            federation=self.federation,
            description=self.description,
            base_resolver=new_resolver,
            permission_classes=self.permission_classes,
            default=self.default_value,
            # ignored because of https://github.com/python/mypy/issues/6910
            default_factory=self.default_factory,  # type: ignore[misc]
            deprecation_reason=self.deprecation_reason,
        )

    def get_result(
        self, source: Any, info: Info, args: List[Any], kwargs: Dict[str, Any]
    ) -> Union[Awaitable[Any], Any]:
        """
        Calls the resolver defined for the StrawberryField. If the field doesn't have a
        resolver defined we default to using getattr on `source`.
        """

        if self.base_resolver:
            return self.base_resolver(*args, **kwargs)

        return getattr(source, self.python_name)

    @property
    def _has_async_permission_classes(self) -> bool:
        for permission_class in self.permission_classes:
            if inspect.iscoroutinefunction(permission_class.has_permission):
                return True
        return False

    @property
    def _has_async_base_resolver(self) -> bool:
        return self.base_resolver is not None and self.base_resolver.is_async

    @cached_property
    def is_async(self) -> bool:
        return self._has_async_permission_classes or self._has_async_base_resolver


T = TypeVar("T")


@overload
def field(
    *,
    resolver: Callable[[], T],
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    federation: Optional[FederationFieldParams] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable, object] = UNSET,
) -> T:
    ...


@overload
def field(
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    init: Literal[True] = True,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    federation: Optional[FederationFieldParams] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable, object] = UNSET,
) -> Any:
    ...


@overload
def field(
    resolver: _RESOLVER_TYPE,
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    federation: Optional[FederationFieldParams] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable, object] = UNSET,
) -> StrawberryField:
    ...


def field(
    resolver=None,
    *,
    name=None,
    is_subscription=False,
    description=None,
    permission_classes=None,
    federation=None,
    deprecation_reason=None,
    default=UNSET,
    default_factory=UNSET,
    # This init parameter is used by PyRight to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init=None,
) -> Any:
    """Annotates a method or property as a GraphQL field.

    This is normally used inside a type declaration:

    >>> @strawberry.type:
    >>> class X:
    >>>     field_abc: str = strawberry.field(description="ABC")

    >>>     @strawberry.field(description="ABC")
    >>>     def field_with_resolver(self) -> str:
    >>>         return "abc"

    it can be used both as decorator and as a normal function.
    """

    field_ = StrawberryField(
        python_name=None,
        graphql_name=name,
        type_annotation=None,
        description=description,
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        federation=federation or FederationFieldParams(),
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
    )

    if resolver:
        assert init is not True, "Can't set init as True when passing a resolver."
        return field_(resolver)
    return field_


def _get_fields(cls: Type) -> List[StrawberryField]:
    """Get all the strawberry fields off a strawberry.type cls

    This function returns a list of StrawberryFields (one for each field item), while
    also paying attention the name and typing of the field.

    StrawberryFields can be defined on a strawberry.type class as either a dataclass-
    style field or using strawberry.field as a decorator.

    >>> import strawberry
    >>> @strawberry.type
    ... class Query:
    ...     type_1a: int = 5
    ...     type_1b: int = strawberry.field(...)
    ...     type_1c: int = strawberry.field(resolver=...)
    ...
    ...     @strawberry.field
    ...     def type_2(self) -> int:
    ...         ...

    Type #1:
        A pure dataclass-style field. Will not have a StrawberryField; one will need to
        be created in this function. Type annotation is required.

    Type #2:
        A field defined using @strawberry.field as a decorator around the resolver. The
        resolver must be type-annotated.

    The StrawberryField.python_name value will be assigned to the field's name on the
    class if one is not set by either using an explicit strawberry.field(name=...) or by
    passing a named function (i.e. not an anonymous lambda) to strawberry.field
    (typically as a decorator).
    """
    # Deferred import to avoid import cycles
    from strawberry.field import StrawberryField

    fields: Dict[str, StrawberryField] = {}

    # before trying to find any fields, let's first add the fields defined in
    # parent classes, we do this by checking if parents have a type definition
    for base in cls.__bases__:
        if hasattr(base, "_type_definition"):
            base_fields = {
                field.python_name: field
                # TODO: we need to rename _fields to something else
                for field in base._type_definition._fields  # type: ignore
            }

            # Add base's fields to cls' fields
            fields = {**fields, **base_fields}

    # Find the class the each field was originally defined on so we can use
    # that scope later when resolving the type, as it may have different names
    # available to it.
    origins: Dict[str, type] = {field_name: cls for field_name in cls.__annotations__}

    for base in cls.__mro__:
        if hasattr(base, "_type_definition"):
            for field in base._type_definition._fields:  # type: ignore
                if field.python_name in base.__annotations__:
                    origins.setdefault(field.name, base)

    # then we can proceed with finding the fields for the current class
    for field in dataclasses.fields(cls):

        if isinstance(field, StrawberryField):
            # Check that the field type is not Private
            if isinstance(field.type, Private):
                raise PrivateStrawberryFieldError(field.python_name, cls.__name__)

            # Check that default is not set if a resolver is defined
            if (
                field.default is not dataclasses.MISSING
                and field.base_resolver is not None
            ):
                raise FieldWithResolverAndDefaultValueError(
                    field.python_name, cls.__name__
                )

            # Check that default_factory is not set if a resolver is defined
            # Note: using getattr because of this issue:
            # https://github.com/python/mypy/issues/6910
            if (
                getattr(field, "default_factory") is not dataclasses.MISSING  # noqa
                and field.base_resolver is not None
            ):
                raise FieldWithResolverAndDefaultFactoryError(
                    field.python_name, cls.__name__
                )

            # we make sure that the origin is either the field's resolver when
            # called as:
            #
            # >>> @strawberry.field
            # ... def x(self): ...
            #
            # or the class where this field was defined, so we always have
            # the correct origin for determining field types when resolving
            # the types.
            field.origin = field.origin or cls

            # Make sure types are StrawberryAnnotations
            if not isinstance(field.type_annotation, StrawberryAnnotation):
                module = sys.modules[field.origin.__module__]
                field.type_annotation = StrawberryAnnotation(
                    annotation=field.type_annotation, namespace=module.__dict__
                )

        # Create a StrawberryField for fields that didn't use strawberry.field
        else:
            # Only ignore Private fields that weren't defined using StrawberryFields
            if isinstance(field.type, Private):
                continue

            field_type = field.type

            origin = origins.get(field.name, cls)
            module = sys.modules[origin.__module__]

            # Create a StrawberryField, for fields of Types #1 and #2a
            field = StrawberryField(
                python_name=field.name,
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    annotation=field_type,
                    namespace=module.__dict__,
                ),
                origin=origin,
                default=getattr(cls, field.name, UNSET),
            )

        field_name = field.python_name

        assert_message = "Field must have a name by the time the schema is generated"
        assert field_name is not None, assert_message

        # TODO: Raise exception if field_name already in fields
        fields[field_name] = field

    return list(fields.values())


__all__ = ["FederationFieldParams", "StrawberryField", "field", "_get_fields"]
