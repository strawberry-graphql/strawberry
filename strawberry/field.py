import dataclasses
import typing
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, Union

from strawberry.arguments import UNSET
from strawberry.types.info import Info
from strawberry.utils.typing import get_parameters, has_type_var, is_type_var

from .arguments import StrawberryArgument
from .permission import BasePermission
from .types.fields.resolver import StrawberryResolver
from .types.types import FederationFieldParams
from .union import StrawberryUnion
from .utils.str_converters import to_camel_case


_RESOLVER_TYPE = Union[StrawberryResolver, Callable]


class StrawberryField(dataclasses.Field):
    def __init__(
        self,
        python_name: Optional[str] = None,
        graphql_name: Optional[str] = None,
        type_: Optional[Union[Type, StrawberryUnion]] = None,
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

        # Note: StrawberryField.default is the same as
        # StrawberryField.default_value except that `.default` uses
        # `dataclasses.MISSING` to represent an "undefined" value and
        # `.default_value` uses `UNSET`
        self.default_value = default

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

    def _get_return_type(self):
        # using type ignore to make mypy happy,
        # this codepath will change in future anyway, so this is ok
        if self.is_list:
            assert self.child

            type_ = List[self.child._get_return_type()]  # type: ignore
        else:
            type_ = self.type

        if self.is_optional:
            type_ = Optional[type_]  # type: ignore

        return type_


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
        type_=None,
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
