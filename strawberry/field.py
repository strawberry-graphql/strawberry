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
)

from cached_property import cached_property  # type: ignore

from strawberry.annotation import StrawberryAnnotation, resolve_annotation
from strawberry.arguments import UNSET, StrawberryArgument
from strawberry.exceptions import UnknownTypeError
from strawberry.type import StrawberryType
from strawberry.types.info import Info
from strawberry.utils.mixins import GraphQLNameMixin

from .permission import BasePermission
from .types.fields.resolver import StrawberryResolver
from .types.types import FederationFieldParams, TypeDefinition


_RESOLVER_TYPE = Union[StrawberryResolver, Callable]


@dataclasses.dataclass
class BareStrawberryArgument:
    """
    Container for a StrawberryArgument where we don't know the argument name
    yet. This lets us create arguments and then bind them to a name later.
    """

    type_annotation: StrawberryAnnotation
    default: Any
    description: Optional[str]

    def as_argument(self, arg_name: str) -> StrawberryArgument:
        return StrawberryArgument(
            python_name=arg_name,
            graphql_name=None,
            type_annotation=self.type_annotation,
            default=self.default,
            description=self.description,
        )


class StrawberryField(dataclasses.Field, GraphQLNameMixin):
    python_name: str

    def __init__(
        self,
        python_name: Optional[str] = None,
        graphql_name: Optional[str] = None,
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

        self._type: Optional[Union[StrawberryType, type]] = None
        self._resolved_type: Optional[Union[StrawberryType, type]] = None

    def __call__(self, resolver: _RESOLVER_TYPE) -> "StrawberryField":
        """Add a resolver to the field"""

        # Allow for StrawberryResolvers or bare functions to be provided
        if not isinstance(resolver, StrawberryResolver):
            resolver = StrawberryResolver(resolver)

        self.base_resolver = resolver

        return self

    @property
    def arguments(self) -> List[StrawberryArgument]:
        arguments_as_types = self.get_field_arguments()

        if not self.base_resolver:
            return []

        # Convert the arguments to StrawberryArgument types
        arguments = []
        for arg_name, type_ in arguments_as_types.items():
            if isinstance(type_, BareStrawberryArgument):
                argument = type_
            else:
                default = self.base_resolver.get_argument_default(arg_name)
                argument = self.create_argument(type_, default)

            arguments.append(argument.as_argument(arg_name))

        return arguments

    def get_field_arguments(self) -> Dict[str, object]:
        """
        Hook to modify the GraphQL arguments for the field
        """
        if not self.base_resolver:
            return {}

        return self.base_resolver.arguments

    def create_argument(
        self,
        type_annotation: object,
        default: Any = UNSET,
        description: Optional[str] = None,
    ) -> BareStrawberryArgument:
        """Helper function to create StrawberryArgument"""
        annotation_namespace = None
        if self.base_resolver:
            annotation_namespace = self.base_resolver.annotation_namespace

        return BareStrawberryArgument(
            type_annotation=StrawberryAnnotation(
                annotation=type_annotation,
                namespace=annotation_namespace,
            ),
            default=default,
            description=description,
        )

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

    @property
    def origin_namespace(self) -> Dict[str, Any]:
        # An origin should be set by now, either from the resolver function or
        # when the type is constructed
        assert self.origin

        module = sys.modules[self.origin.__module__]
        namespace = module.__dict__
        return namespace

    def get_return_type(self) -> Union[object, str]:
        """
        Hook to allow custom fields to modify the return type of a field. This
        hook should only be called once at schema creation time.

        Note: we make sure that the type is resolved so that it's easier to deal
        with in custom fields.

        For example:

        class MyCustomField(StrawberryField):
            def get_return_type(self):
                type_ = super().get_return_type()
                assert type_ == Optional[str]
                return str

        @strawberry.type
        class Query:
            @MyCustomField()
            def my_field(self) -> "Optional[str]":
                return "foo"
        """

        type_ = self.type
        try:
            evaled_type = resolve_annotation(type_, self.origin_namespace)
        except NameError as error:
            raise UnknownTypeError(self, str(error))

        return evaled_type

    @property
    def resolved_type(self) -> Union[StrawberryType, type]:
        if self._resolved_type:
            return self._resolved_type

        type_ = self.get_return_type()

        type_annotation = StrawberryAnnotation(
            annotation=type_, namespace=self.origin_namespace
        )

        resolved_type = type_annotation.resolve()

        self._resolved_type = resolved_type
        return self._resolved_type

    @property  # type: ignore
    def type(self) -> Optional[Union[object, str]]:  # type: ignore
        if self.base_resolver is not None:
            # Handle unannotated functions (such as lambdas)
            if self.base_resolver.type is not None:
                return self.base_resolver.type

        return self._type

    @type.setter
    def type(self, type_: Any) -> None:
        self._type = type_

    # TODO: add this to arguments (and/or move it to StrawberryType)
    @property
    def type_params(self) -> List[TypeVar]:
        if hasattr(self.type, "_type_definition"):
            parameters = getattr(self.type, "__parameters__", None)

            return list(parameters) if parameters else []

        # TODO: Consider making leaf types always StrawberryTypes, maybe a
        #       StrawberryBaseType or something
        if isinstance(self.resolved_type, StrawberryType):
            return self.resolved_type.type_params
        return []

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, builtins.type]]
    ) -> "StrawberryField":
        new_type: Union[StrawberryType, type]
        resolved_type = self.resolved_type

        # TODO: Remove with creation of StrawberryObject. Will act same as other
        #       StrawberryTypes
        if hasattr(resolved_type, "_type_definition"):
            type_definition: TypeDefinition = (
                resolved_type._type_definition  # type: ignore
            )

            if type_definition.is_generic:
                type_ = type_definition
                new_type = type_.copy_with(type_var_map)
        else:
            assert isinstance(resolved_type, StrawberryType)

            new_type = resolved_type.copy_with(type_var_map)

        new_resolver = (
            self.base_resolver.copy_with(type_var_map)
            if self.base_resolver is not None
            else None
        )

        field = StrawberryField(
            python_name=self.python_name,
            graphql_name=self.graphql_name,
            # TODO: do we need to wrap this in `StrawberryAnnotation`?
            # see comment related to dataclasses above
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
        field.type = new_type
        return field

    def get_result(
        self, source: Any, info: Info, arguments: Dict[str, Any]
    ) -> Union[Awaitable[Any], Any]:
        """
        Calls the resolver defined for the StrawberryField. If the field doesn't have a
        resolver defined we default to using getattr on `source`.
        """

        if self.base_resolver:
            args = []
            if self.base_resolver.has_self_arg:
                args = [source]
            return self.base_resolver(*args, **arguments)

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


def field(
    resolver: Optional[_RESOLVER_TYPE] = None,
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
        description=description,
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        federation=federation or FederationFieldParams(),
        deprecation_reason=deprecation_reason,
        default=default,
        default_factory=default_factory,
    )

    if resolver:
        return field_(resolver)
    return field_


__all__ = ["FederationFieldParams", "StrawberryField", "field"]
