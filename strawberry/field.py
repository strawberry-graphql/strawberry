import builtins
import dataclasses
import enum
from inspect import iscoroutine
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from graphql import GraphQLResolveInfo

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import UNSET, convert_arguments
from strawberry.type import StrawberryList, StrawberryType
from strawberry.types.info import Info

from .arguments import StrawberryArgument
from .permission import BasePermission
from .types.fields.resolver import StrawberryResolver
from .types.types import FederationFieldParams, TypeDefinition
from .utils.str_converters import to_camel_case


_RESOLVER_TYPE = Union[StrawberryResolver, Callable]


class StrawberryField(dataclasses.Field):
    def __init__(
        self,
        python_name: Optional[str],
        graphql_name: Optional[str],
        type_annotation: Optional[StrawberryAnnotation],
        origin: Optional[Union[Type, Callable]] = None,
        is_subscription: bool = False,
        federation: FederationFieldParams = None,
        description: Optional[str] = None,
        base_resolver: Optional[StrawberryResolver] = None,
        permission_classes: List[Type[BasePermission]] = (),  # type: ignore
        default_value: Any = UNSET,
        default_factory: Union[Callable, object] = UNSET,
        deprecation_reason: Optional[str] = None,
    ):
        federation = federation or FederationFieldParams()

        # basic fields are fields with no provided resolver
        is_basic_field = not base_resolver

        super().__init__(  # type: ignore
            default=(default_value if default_value != UNSET else dataclasses.MISSING),
            default_factory=(
                default_factory if default_factory != UNSET else dataclasses.MISSING
            ),
            init=is_basic_field,
            repr=is_basic_field,
            compare=is_basic_field,
            hash=None,
            metadata=None,
        )

        self._graphql_name = graphql_name
        if python_name is not None:
            self.python_name = python_name

        self.type_annotation = type_annotation

        self.description: Optional[str] = description
        self.origin: Optional[Union[Type, Callable]] = origin

        self._base_resolver: Optional[StrawberryResolver] = None
        if base_resolver is not None:
            self.base_resolver = base_resolver

        self.default_value = default_value
        self.is_subscription = is_subscription

        self.federation: FederationFieldParams = federation
        self.permission_classes: List[Type[BasePermission]] = list(permission_classes)

        self.deprecation_reason = deprecation_reason

    def __call__(self, resolver: _RESOLVER_TYPE) -> "StrawberryField":
        """Add a resolver to the field"""

        # Allow for StrawberryResolvers or bare functions to be provided
        if not isinstance(resolver, StrawberryResolver):
            resolver = StrawberryResolver(resolver)

        self.base_resolver = resolver

        return self

    @property
    def arguments(self) -> List[StrawberryArgument]:
        if not self.base_resolver:
            return []

        return self.base_resolver.arguments

    @property
    def graphql_name(self) -> Optional[str]:
        if self._graphql_name:
            return self._graphql_name
        if self.python_name:
            return to_camel_case(self.python_name)
        if self.base_resolver:
            return to_camel_case(self.base_resolver.name)
        return None

    @property
    def python_name(self) -> str:
        return self.name

    @python_name.setter
    def python_name(self, name: str) -> None:
        self.name = name

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

    def _get_arguments(
        self,
        source: Any,
        info: Any,
        kwargs: Dict[str, Any],
    ) -> Tuple[List[Any], Dict[str, Any]]:
        assert self.base_resolver is not None

        kwargs = convert_arguments(kwargs, self.arguments)

        # the following code allows to omit info and root arguments
        # by inspecting the original resolver arguments,
        # if it asks for self, the source will be passed as first argument
        # if it asks for root, the source it will be passed as kwarg
        # if it asks for info, the info will be passed as kwarg

        args = []

        if self.base_resolver.has_self_arg:
            args.append(source)

        if self.base_resolver.has_root_arg:
            kwargs["root"] = source

        if self.base_resolver.has_info_arg:
            kwargs["info"] = info

        return args, kwargs

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
                type_copy = type_.copy_with(type_var_map)

                new_type = builtins.type(
                    type_copy.name,
                    (),
                    {"_type_definition": type_copy},
                )

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
            default_value=self.default_value,
            # ignored because of https://github.com/python/mypy/issues/6910
            default_factory=self.default_factory,  # type: ignore[misc]
            deprecation_reason=self.deprecation_reason,
        )

    def get_result(
        self, source: Any, info: Any, kwargs: Dict[str, Any]
    ) -> Union[Awaitable[Any], Any]:
        """
        Calls the resolver defined for the StrawberryField. If the field doesn't have a
        resolver defined we default to using getattr on `source`.
        """

        if self.base_resolver:
            args, kwargs = self._get_arguments(source, info=info, kwargs=kwargs)

            return self.base_resolver(*args, **kwargs)

        return getattr(source, self.python_name)

    def get_wrapped_resolver(self) -> Callable:
        # TODO: This could potentially be handled by StrawberryResolver in the future
        def _check_permissions(source: Any, info: Info, kwargs: Dict[str, Any]):
            """
            Checks if the permission should be accepted and
            raises an exception if not
            """
            for permission_class in self.permission_classes:
                permission = permission_class()

                if not permission.has_permission(source, info, **kwargs):
                    message = getattr(permission, "message", None)
                    raise PermissionError(message)

        def _convert_enums_to_values(type_: StrawberryType, result: Any) -> Any:
            # graphql-core expects a resolver for an Enum type to return
            # the enum's *value* (not its name or an instance of the enum).

            # short circuit to skip checks when result is None (i.e. Optional[Enum])
            if result is None:
                return result

            if isinstance(result, enum.Enum):
                return result.value

            if isinstance(type_, StrawberryList):
                return [
                    _convert_enums_to_values(type_.of_type, item) for item in result
                ]

            return result

        def _strawberry_info_from_graphql(info: GraphQLResolveInfo) -> Info:
            return Info(
                field_name=info.field_name,
                field_nodes=info.field_nodes,
                context=info.context,
                root_value=info.root_value,
                variable_values=info.variable_values,
                return_type=self.type,
                operation=info.operation,
                path=info.path,
            )

        def _resolver(_source: Any, info: GraphQLResolveInfo, **kwargs):
            strawberry_info = _strawberry_info_from_graphql(info)
            _check_permissions(_source, strawberry_info, kwargs)

            result = self.get_result(_source, info=strawberry_info, kwargs=kwargs)

            if iscoroutine(result):  # pragma: no cover

                async def await_result(result):
                    return _convert_enums_to_values(self.type, await result)

                return await_result(result)

            result = _convert_enums_to_values(self.type, result)
            return result

        _resolver._is_default = not self.base_resolver  # type: ignore
        return _resolver


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
        type_annotation=None,
        description=description,
        is_subscription=is_subscription,
        permission_classes=permission_classes or [],
        federation=federation or FederationFieldParams(),
        deprecation_reason=deprecation_reason,
        default_value=default,
        default_factory=default_factory,
    )

    if resolver:
        return field_(resolver)
    return field_


__all__ = ["FederationFieldParams", "StrawberryField", "field"]
