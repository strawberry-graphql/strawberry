import dataclasses
import enum
import typing
from inspect import iscoroutine
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Type, Union

from graphql import GraphQLResolveInfo

from strawberry.arguments import convert_arguments
from strawberry.types.info import Info
from strawberry.utils.typing import get_parameters, has_type_var, is_type_var

from .arguments import StrawberryArgument
from .permission import BasePermission
from .types.fields.resolver import StrawberryResolver
from .types.types import FederationFieldParams, undefined
from .union import StrawberryUnion
from .utils.str_converters import to_camel_case


_RESOLVER_TYPE = Union[StrawberryResolver, Callable]


class StrawberryField(dataclasses.Field):
    def __init__(
        self,
        python_name: Optional[str],
        graphql_name: Optional[str],
        type_: Optional[Union[Type, StrawberryUnion]],
        origin: Optional[Union[Type, Callable]] = None,
        child: Optional["StrawberryField"] = None,
        is_subscription: bool = False,
        is_optional: bool = False,
        is_child_optional: bool = False,
        is_list: bool = False,
        is_union: bool = False,
        federation: FederationFieldParams = None,
        description: Optional[str] = None,
        base_resolver: Optional[StrawberryResolver] = None,
        permission_classes: List[Type[BasePermission]] = (),  # type: ignore
        default_value: Any = undefined,
        deprecation_reason: Optional[str] = None,
    ):
        federation = federation or FederationFieldParams()

        # basic fields are fields with no provided resolver
        is_basic_field = not base_resolver

        super().__init__(  # type: ignore
            default=dataclasses.MISSING,
            default_factory=dataclasses.MISSING,
            init=is_basic_field,
            repr=is_basic_field,
            compare=is_basic_field,
            hash=None,
            metadata=None,
        )

        self._graphql_name = graphql_name
        if python_name is not None:
            self.python_name = python_name
        if type_ is not None:
            # TODO: Clean up the typing around StrawberryField.type
            self.type = typing.cast(type, type_)

        self.description: Optional[str] = description
        self.origin: Optional[Union[Type, Callable]] = origin

        self._base_resolver: Optional[StrawberryResolver] = None
        if base_resolver is not None:
            self.base_resolver = base_resolver

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

        self.base_resolver = resolver
        self.type = resolver.type

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

    @property
    def type_params(self) -> Optional[List[Type]]:
        if self.is_list:
            assert self.child is not None
            return self.child.type_params

        if isinstance(self.type, StrawberryUnion):
            types = self.type.types
            type_vars = [t for t in types if is_type_var(t)]

            if type_vars:
                return type_vars

        if is_type_var(self.type):
            return [self.type]

        if has_type_var(self.type):
            return get_parameters(self.type)

        return None

    def _get_arguments(
        self, kwargs: Dict[str, Any], source: Any, info: Any
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

    def get_result(
        self, kwargs: Dict[str, Any], source: Any, info: Any
    ) -> Union[Awaitable[Any], Any]:
        """
        Calls the resolver defined for the StrawberryField. If the field doesn't have a
        resolver defined we default to using getattr on `source`.
        """

        if self.base_resolver:
            args, kwargs = self._get_arguments(kwargs, source=source, info=info)

            return self.base_resolver(*args, **kwargs)

        return getattr(source, self.python_name)

    def get_wrapped_resolver(self) -> Callable:
        # TODO: This could potentially be handled by StrawberryResolver in the future
        def _check_permissions(source, info: Info, **kwargs):
            """
            Checks if the permission should be accepted and
            raises an exception if not
            """
            for permission_class in self.permission_classes:
                permission = permission_class()

                if not permission.has_permission(source, info, **kwargs):
                    message = getattr(permission, "message", None)
                    raise PermissionError(message)

        def _convert_enums_to_values(field_: StrawberryField, result: Any) -> Any:
            # graphql-core expects a resolver for an Enum type to return
            # the enum's *value* (not its name or an instance of the enum).

            # short circuit to skip checks when result is falsy
            if not result:
                return result

            if isinstance(result, enum.Enum):
                return result.value

            if field_.is_list:
                assert self.child is not None
                return [_convert_enums_to_values(self.child, item) for item in result]

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

        def _resolver(source, info: GraphQLResolveInfo, **kwargs):
            strawberry_info = _strawberry_info_from_graphql(info)
            _check_permissions(source, strawberry_info, **kwargs)

            result = self.get_result(kwargs=kwargs, info=strawberry_info, source=source)

            if iscoroutine(result):  # pragma: no cover

                async def await_result(result):
                    return _convert_enums_to_values(self, await result)

                return await_result(result)

            result = _convert_enums_to_values(self, result)
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
