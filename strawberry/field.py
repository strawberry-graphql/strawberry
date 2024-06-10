from __future__ import annotations

import contextlib
import copy
import dataclasses
import sys
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Coroutine,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import InvalidArgumentTypeError, InvalidDefaultFactoryError
from strawberry.type import (
    StrawberryType,
    WithStrawberryObjectDefinition,
    has_object_definition,
)
from strawberry.union import StrawberryUnion

from .types.fields.resolver import StrawberryResolver

if TYPE_CHECKING:
    import builtins
    from typing_extensions import Literal, Self

    from strawberry.arguments import StrawberryArgument
    from strawberry.extensions.field_extension import FieldExtension
    from strawberry.types.info import Info
    from strawberry.types.types import StrawberryObjectDefinition

    from .permission import BasePermission

T = TypeVar("T")

_RESOLVER_TYPE_SYNC = Union[
    StrawberryResolver[T],
    Callable[..., T],
    "staticmethod[Any, T]",
    "classmethod[Any, Any, T]",
]

_RESOLVER_TYPE_ASYNC = Union[
    Callable[..., Coroutine[Any, Any, T]],
    Callable[..., Awaitable[T]],
]

_RESOLVER_TYPE = Union[_RESOLVER_TYPE_SYNC[T], _RESOLVER_TYPE_ASYNC[T]]

UNRESOLVED = object()


def _is_generic(resolver_type: Union[StrawberryType, type]) -> bool:
    """Returns True if `resolver_type` is generic else False"""
    if isinstance(resolver_type, StrawberryType):
        return resolver_type.is_graphql_generic

    # solves the Generic subclass case
    if has_object_definition(resolver_type):
        return resolver_type.__strawberry_definition__.is_graphql_generic

    return False


class StrawberryField(dataclasses.Field):
    type_annotation: Optional[StrawberryAnnotation]
    default_resolver: Callable[[Any, str], object] = getattr

    def __init__(
        self,
        python_name: Optional[str] = None,
        graphql_name: Optional[str] = None,
        type_annotation: Optional[StrawberryAnnotation] = None,
        origin: Optional[Union[Type, Callable, staticmethod, classmethod]] = None,
        is_subscription: bool = False,
        description: Optional[str] = None,
        base_resolver: Optional[StrawberryResolver] = None,
        permission_classes: List[Type[BasePermission]] = (),  # type: ignore
        default: object = dataclasses.MISSING,
        default_factory: Union[Callable[[], Any], object] = dataclasses.MISSING,
        metadata: Optional[Mapping[Any, Any]] = None,
        deprecation_reason: Optional[str] = None,
        directives: Sequence[object] = (),
        extensions: List[FieldExtension] = (),  # type: ignore
    ) -> None:
        # basic fields are fields with no provided resolver
        is_basic_field = not base_resolver

        kwargs: Any = {}

        # kw_only was added to python 3.10 and it is required
        if sys.version_info >= (3, 10):
            kwargs["kw_only"] = dataclasses.MISSING

        super().__init__(
            default=default,
            default_factory=default_factory,  # type: ignore
            init=is_basic_field,
            repr=is_basic_field,
            compare=is_basic_field,
            hash=None,
            metadata=metadata or {},
            **kwargs,
        )

        self.graphql_name = graphql_name
        if python_name is not None:
            self.python_name = python_name

        self.type_annotation = type_annotation

        self.description: Optional[str] = description
        self.origin = origin

        self._arguments: Optional[List[StrawberryArgument]] = None
        self._base_resolver: Optional[StrawberryResolver] = None
        if base_resolver is not None:
            self.base_resolver = base_resolver

        # Note: StrawberryField.default is the same as
        # StrawberryField.default_value except that `.default` uses
        # `dataclasses.MISSING` to represent an "undefined" value and
        # `.default_value` uses `UNSET`
        self.default_value = default
        if callable(default_factory):
            try:
                self.default_value = default_factory()
            except TypeError as exc:
                raise InvalidDefaultFactoryError from exc

        self.is_subscription = is_subscription

        self.permission_classes: List[Type[BasePermission]] = list(permission_classes)
        self.directives = list(directives)
        self.extensions: List[FieldExtension] = list(extensions)

        # Automatically add the permissions extension
        if len(self.permission_classes):
            from .permission import PermissionExtension

            if not self.extensions:
                self.extensions = []
            permission_instances = [
                permission_class() for permission_class in permission_classes
            ]
            # Append to make it run first (last is outermost)
            self.extensions.append(
                PermissionExtension(permission_instances, use_directives=False)
            )
        self.deprecation_reason = deprecation_reason

    def __copy__(self) -> Self:
        new_field = type(self)(
            python_name=self.python_name,
            graphql_name=self.graphql_name,
            type_annotation=self.type_annotation,
            origin=self.origin,
            is_subscription=self.is_subscription,
            description=self.description,
            base_resolver=self.base_resolver,
            permission_classes=(
                self.permission_classes[:]
                if self.permission_classes is not None
                else []
            ),
            default=self.default_value,
            default_factory=self.default_factory,
            metadata=self.metadata.copy() if self.metadata is not None else None,
            deprecation_reason=self.deprecation_reason,
            directives=self.directives[:] if self.directives is not None else [],
            extensions=self.extensions[:] if self.extensions is not None else [],
        )
        new_field._arguments = (
            self._arguments[:] if self._arguments is not None else None
        )
        return new_field

    def __call__(self, resolver: _RESOLVER_TYPE) -> Self:
        """Add a resolver to the field"""

        # Allow for StrawberryResolvers or bare functions to be provided
        if not isinstance(resolver, StrawberryResolver):
            resolver = StrawberryResolver(resolver)

        for argument in resolver.arguments:
            if isinstance(argument.type_annotation.annotation, str):
                continue
            elif isinstance(argument.type, StrawberryUnion):
                raise InvalidArgumentTypeError(
                    resolver,
                    argument,
                )
            elif has_object_definition(argument.type):
                if argument.type.__strawberry_definition__.is_interface:
                    raise InvalidArgumentTypeError(
                        resolver,
                        argument,
                    )

        self.base_resolver = resolver

        return self

    def get_result(
        self, source: Any, info: Optional[Info], args: List[Any], kwargs: Any
    ) -> Union[Awaitable[Any], Any]:
        """
        Calls the resolver defined for the StrawberryField.
        If the field doesn't have a resolver defined we default
        to using the default resolver specified in StrawberryConfig.
        """

        if self.base_resolver:
            return self.base_resolver(*args, **kwargs)

        return self.default_resolver(source, self.python_name)

    @property
    def is_basic_field(self) -> bool:
        """
        Flag indicating if this is a "basic" field that has no resolver or
        permission classes, i.e. it just returns the relevant attribute from
        the source object. If it is a basic field we can avoid constructing
        an `Info` object and running any permission checks in the resolver
        which improves performance.
        """
        return not self.base_resolver and not self.extensions

    @property
    def arguments(self) -> List[StrawberryArgument]:
        if self._arguments is None:
            self._arguments = self.base_resolver.arguments if self.base_resolver else []

        return self._arguments

    @arguments.setter
    def arguments(self, value: List[StrawberryArgument]) -> None:
        self._arguments = value

    @property
    def is_graphql_generic(self) -> bool:
        return (
            self.base_resolver.is_graphql_generic
            if self.base_resolver
            else _is_generic(self.type)
        )

    def _python_name(self) -> Optional[str]:
        if self.name:
            return self.name

        if self.base_resolver:
            return self.base_resolver.name

        return None

    def _set_python_name(self, name: str) -> None:
        self.name = name

    python_name: str = property(_python_name, _set_python_name)  # type: ignore[assignment]

    @property
    def base_resolver(self) -> Optional[StrawberryResolver]:
        return self._base_resolver

    @base_resolver.setter
    def base_resolver(self, resolver: StrawberryResolver) -> None:
        self._base_resolver = resolver

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
    def type(
        self,
    ) -> Union[  # type: ignore [valid-type]
        StrawberryType,
        Type[WithStrawberryObjectDefinition],
        Literal[UNRESOLVED],
    ]:
        return self.resolve_type()

    @type.setter
    def type(self, type_: Any) -> None:
        # Note: we aren't setting a namespace here for the annotation. That
        # happens in the `_get_fields` function in `types/type_resolver` so
        # that we have access to the correct namespace for the object type
        # the field is attached to.
        self.type_annotation = StrawberryAnnotation.from_annotation(
            type_, namespace=None
        )

    # TODO: add this to arguments (and/or move it to StrawberryType)
    @property
    def type_params(self) -> List[TypeVar]:
        if has_object_definition(self.type):
            parameters = getattr(self.type, "__parameters__", None)

            return list(parameters) if parameters else []

        # TODO: Consider making leaf types always StrawberryTypes, maybe a
        #       StrawberryBaseType or something
        if isinstance(self.type, StrawberryType):
            return self.type.type_params
        return []

    def resolve_type(
        self,
        *,
        type_definition: Optional[StrawberryObjectDefinition] = None,
    ) -> Union[  # type: ignore [valid-type]
        StrawberryType,
        Type[WithStrawberryObjectDefinition],
        Literal[UNRESOLVED],
    ]:
        # We return UNRESOLVED by default, which means this case will raise a
        # MissingReturnAnnotationError exception in _check_field_annotations
        resolved = UNRESOLVED

        # We are catching NameError because dataclasses tries to fetch the type
        # of the field from the class before the class is fully defined.
        # This triggers a NameError error when using forward references because
        # our `type` property tries to find the field type from the global namespace
        # but it is not yet defined.
        with contextlib.suppress(NameError):
            # Prioritise the field type over the resolver return type
            if self.type_annotation is not None:
                resolved = self.type_annotation.resolve()
            elif self.base_resolver is not None and self.base_resolver.type is not None:
                # Handle unannotated functions (such as lambdas)
                # Generics will raise MissingTypesForGenericError later
                # on if we let it be returned. So use `type_annotation` instead
                # which is the same behaviour as having no type information.
                resolved = self.base_resolver.type

        # If this is a generic field, try to resolve it using its origin's
        # specialized type_var_map
        # TODO: should we check arguments here too?
        if _is_generic(resolved):  # type: ignore
            specialized_type_var_map = (
                type_definition and type_definition.specialized_type_var_map
            )
            if specialized_type_var_map and isinstance(resolved, StrawberryType):
                resolved = resolved.copy_with(specialized_type_var_map)

            # If the field is still generic, try to resolve it from the type_definition
            # that is asking for it.
            if (
                _is_generic(cast(Union[StrawberryType, type], resolved))
                and type_definition is not None
                and type_definition.type_var_map
                and isinstance(resolved, StrawberryType)
            ):
                resolved = resolved.copy_with(type_definition.type_var_map)

        return resolved

    def copy_with(
        self, type_var_map: Mapping[str, Union[StrawberryType, builtins.type]]
    ) -> Self:
        new_field = copy.copy(self)

        override_type: Optional[
            Union[StrawberryType, Type[WithStrawberryObjectDefinition]]
        ] = None
        type_ = self.resolve_type()
        if has_object_definition(type_):
            type_definition = type_.__strawberry_definition__

            if type_definition.is_graphql_generic:
                type_ = type_definition
                override_type = type_.copy_with(type_var_map)
        elif isinstance(type_, StrawberryType):
            override_type = type_.copy_with(type_var_map)

        if override_type is not None:
            new_field.type_annotation = StrawberryAnnotation(
                override_type,
                namespace=(
                    self.type_annotation.namespace if self.type_annotation else None
                ),
            )

        if self.base_resolver is not None:
            new_field.base_resolver = self.base_resolver.copy_with(type_var_map)

        return new_field

    @property
    def _has_async_base_resolver(self) -> bool:
        return self.base_resolver is not None and self.base_resolver.is_async

    @cached_property
    def is_async(self) -> bool:
        return self._has_async_base_resolver


# NOTE: we are separating the sync and async resolvers because using both
# in the same function will cause mypy to raise an error. Not sure if it is a bug


@overload
def field(
    *,
    resolver: _RESOLVER_TYPE_ASYNC[T],
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> T: ...


@overload
def field(
    *,
    resolver: _RESOLVER_TYPE_SYNC[T],
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> T: ...


@overload
def field(
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    init: Literal[True] = True,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> Any: ...


@overload
def field(
    resolver: _RESOLVER_TYPE_ASYNC[T],
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> StrawberryField: ...


@overload
def field(
    resolver: _RESOLVER_TYPE_SYNC[T],
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
) -> StrawberryField: ...


def field(
    resolver: Optional[_RESOLVER_TYPE[Any]] = None,
    *,
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    extensions: Optional[List[FieldExtension]] = None,
    graphql_type: Optional[Any] = None,
    # This init parameter is used by PyRight to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False, None] = None,
) -> Any:
    """Annotates a method or property as a GraphQL field.

    This is normally used inside a type declaration:

    >>> @strawberry.type
    >>> class X:
    >>>     field_abc: str = strawberry.field(description="ABC")

    >>>     @strawberry.field(description="ABC")
    >>>     def field_with_resolver(self) -> str:
    >>>         return "abc"

    it can be used both as decorator and as a normal function.
    """

    type_annotation = StrawberryAnnotation.from_annotation(graphql_type)

    field_ = StrawberryField(
        python_name=None,
        graphql_name=name,
        type_annotation=type_annotation,
        description=description,
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
        metadata=metadata,
        directives=directives or (),
        extensions=extensions or [],
    )

    if resolver:
        assert init is not True, "Can't set init as True when passing a resolver."
        return field_(resolver)
    return field_


__all__ = ["StrawberryField", "field"]
