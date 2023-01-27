import builtins
import dataclasses
import inspect
import sys
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    overload,
)
from typing_extensions import Literal

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.exceptions import InvalidArgumentTypeError, InvalidDefaultFactoryError
from strawberry.type import StrawberryType
from strawberry.types.info import Info
from strawberry.union import StrawberryUnion
from strawberry.utils.cached_property import cached_property

from .permission import BasePermission
from .types.fields.resolver import StrawberryResolver

if TYPE_CHECKING:
    from .object_type import TypeDefinition

T = TypeVar("T")


_RESOLVER_TYPE = Union[
    StrawberryResolver[T],
    Callable[..., T],
    "staticmethod[T]",
    "classmethod[T]",
]


UNRESOLVED = object()


def _is_generic(resolver_type: Union[StrawberryType, type]) -> bool:
    """Returns True if `resolver_type` is generic else False"""
    if isinstance(resolver_type, StrawberryType):
        return resolver_type.is_generic

    # solves the Generic subclass case
    if hasattr(resolver_type, "_type_definition"):
        return resolver_type._type_definition.is_generic

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
    ):
        # basic fields are fields with no provided resolver
        is_basic_field = not base_resolver

        kwargs: Dict[str, Any] = {}

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
                raise InvalidDefaultFactoryError() from exc

        self.is_subscription = is_subscription

        self.permission_classes: List[Type[BasePermission]] = list(permission_classes)
        self.directives = directives

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
                raise InvalidArgumentTypeError(
                    resolver,
                    argument,
                )
            elif getattr(argument.type, "_type_definition", False):
                if argument.type._type_definition.is_interface:  # type: ignore
                    raise InvalidArgumentTypeError(
                        resolver,
                        argument,
                    )

        self.base_resolver = resolver

        return self

    def get_result(
        self, source: Any, info: Optional[Info], args: List[Any], kwargs: Dict[str, Any]
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
        return not self.base_resolver and not self.permission_classes

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

    python_name: str = property(_python_name, _set_python_name)  # type: ignore[assignment]  # noqa: E501

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
    def type(self) -> Union[StrawberryType, type, Literal[UNRESOLVED]]:  # type: ignore
        # We are catching NameError because dataclasses tries to fetch the type
        # of the field from the class before the class is fully defined.
        # This triggers a NameError error when using forward references because
        # our `type` property tries to find the field type from the global namespace
        # but it is not yet defined.
        try:
            # Prioritise the field type over the resolver return type
            if self.type_annotation is not None:
                return self.type_annotation.resolve()

            if self.base_resolver is not None:
                # Handle unannotated functions (such as lambdas)
                if self.base_resolver.type is not None:

                    # Generics will raise MissingTypesForGenericError later
                    # on if we let it be returned. So use `type_annotation` instead
                    # which is the same behaviour as having no type information.
                    if not _is_generic(self.base_resolver.type):
                        return self.base_resolver.type

            # If we get this far it means that we don't have a field type and
            # the resolver doesn't have a return type so all we can do is return
            # UNRESOLVED here.
            # This case will raise a MissingReturnAnnotationError exception in the
            # _check_field_annotations function:
            # https://github.com/strawberry-graphql/strawberry/blob/846f060a63cb568b3cdc0deb26c308a8d0718190/strawberry/object_type.py#L76-L80
            return UNRESOLVED

        except NameError:
            return UNRESOLVED

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
        new_type: Union[StrawberryType, type] = self.type

        # TODO: Remove with creation of StrawberryObject. Will act same as other
        #       StrawberryTypes
        if hasattr(self.type, "_type_definition"):
            type_definition: TypeDefinition = self.type._type_definition

            if type_definition.is_generic:
                type_ = type_definition
                new_type = type_.copy_with(type_var_map)
        elif isinstance(self.type, StrawberryType):
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
            description=self.description,
            base_resolver=new_resolver,
            permission_classes=self.permission_classes,
            default=self.default_value,
            # ignored because of https://github.com/python/mypy/issues/6910
            default_factory=self.default_factory,
            deprecation_reason=self.deprecation_reason,
        )

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


@overload
def field(
    *,
    resolver: _RESOLVER_TYPE[T],
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
    graphql_type: Optional[Any] = None,
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
    deprecation_reason: Optional[str] = None,
    default: Any = dataclasses.MISSING,
    default_factory: Union[Callable[..., object], object] = dataclasses.MISSING,
    metadata: Optional[Mapping[Any, Any]] = None,
    directives: Optional[Sequence[object]] = (),
    graphql_type: Optional[Any] = None,
) -> Any:
    ...


@overload
def field(
    resolver: _RESOLVER_TYPE[T],
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
    graphql_type: Optional[Any] = None,
) -> StrawberryField:
    ...


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
    graphql_type: Optional[Any] = None,
    # This init parameter is used by PyRight to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init: Literal[True, False, None] = None,
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
    )

    if resolver:
        assert init is not True, "Can't set init as True when passing a resolver."
        return field_(resolver)
    return field_


__all__ = ["StrawberryField", "field"]
