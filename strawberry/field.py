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

from backports.cached_property import cached_property
from typing_extensions import Literal, T

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.exceptions import (
    FieldWithResolverAndDefaultFactoryError,
    FieldWithResolverAndDefaultValueError,
    InvalidDefaultFactoryError,
    InvalidFieldArgument,
    MissingFieldAnnotationError,
    MissingReturnAnnotationError,
    PrivateStrawberryFieldError,
)
from strawberry.type import StrawberryType
from strawberry.types.info import Info
from strawberry.union import StrawberryUnion
from strawberry.unset import UNSET

from .permission import BasePermission
from .private import is_private
from .types.fields.resolver import StrawberryResolver


if TYPE_CHECKING:
    from .object_type import TypeDefinition

_RESOLVER_TYPE = Union[StrawberryResolver, Callable, staticmethod, classmethod]

UNRESOLVED = object()


@dataclasses.dataclass
class StrawberryField:
    python_name: Optional[str]
    graphql_name: Optional[str]
    type_annotation: Optional[StrawberryAnnotation] = None
    origin: Optional[Type] = None
    base_resolver: Optional[StrawberryResolver] = None
    arguments: List[StrawberryArgument] = dataclasses.field(default_factory=list)
    is_subscription: bool = False
    description: Optional[str] = None
    deprecation_reason: Optional[str] = None
    permission_classes: List[Type[BasePermission]] = dataclasses.field(
        default_factory=list
    )
    directives: Sequence[object] = ()

    is_basic_field: bool = False  # True if no resolver provided.

    # dataclasses.Field stuff
    default: object = UNSET
    default_factory: Union[Callable[[], Any], object] = UNSET
    default_value: Any = dataclasses.field(init=False, default=UNSET)

    def __call__(
        self,
        evolvable: Union[
            Callable,
            StrawberryResolver,
            staticmethod,
            classmethod,
            Type,
            "StrawberryField",
        ],
    ) -> "StrawberryField":
        # TODO: document this.
        """
        Hack for fields that wasn't provided with a resolver function.
        or for solving usecases like this:
        >>> @strawberry.field(description="bar")
        >>> def foo():
        >>>     ...
        This cannot be handled normally by `strawberry.field`.

        if it was used as a decorator, it would be evaluated when python will
        call the decorator. if it was use as:
        >>> foo: str = strawberry.field(description="bar")
        it would be evaluated in the @strawberry.type fields parsing.
        """
        # TODO: document this.
        # using replace to call __init__ this is a replacement for a frozen style class.

        # if it is a StrawberryResolver
        if isinstance(evolvable, StrawberryResolver):
            return dataclasses.replace(self, base_resolver=evolvable)

        # if it is a type and not a resolver.
        elif inspect.isclass(evolvable):
            return dataclasses.replace(self, origin=evolvable)

        # finally if it is a plain function then create a StrawberryResolver out of it.
        elif callable(evolvable):
            evolvable = StrawberryResolver(evolvable)
            return dataclasses.replace(self, base_resolver=evolvable)

    def __post_init__(self):
        if self.origin:
            assert (
                self.python_name
            ), "Python name must exist set when origin has been determined"
            if self.base_resolver:
                self._evaluate_from_base_resolver()

            else:
                self._evaluate_as_basic_field()

    def _evaluate_from_base_resolver(self) -> None:
        """
        called by __init__ if there is a base resolver and an origin.
        """

        # validate base_resolver
        if not isinstance(self.base_resolver, StrawberryResolver):
            self.base_resolver = StrawberryResolver(self.base_resolver)

        for argument in self.base_resolver.arguments:
            if isinstance(argument.type_annotation.annotation, str):
                continue
            elif isinstance(argument.type, StrawberryUnion):
                raise InvalidFieldArgument(
                    self.base_resolver.name,
                    argument.python_name,
                    "Union",
                )

            elif type_def := getattr(argument.type, "__strawberry_definition__", False):
                if type_def.is_interface:  # type: ignore
                    raise InvalidFieldArgument(
                        self.base_resolver.name,
                        argument.python_name,
                        "Interface",
                    )

        # fetching type annotation
        class_annotation = self.origin.__annotations__.get(self.python_name, False)
        if resolver_annotation := self.base_resolver.type_annotation:
            # solving aliased imports from other modules
            namespace = resolver_annotation.namespace
            namespace.update(sys.modules[self.origin.__module__].__dict__)
            if class_annotation:
                assert (
                    StrawberryAnnotation(
                        class_annotation, namespace=namespace
                    ).safe_resolve()
                    == resolver_annotation.safe_resolve()
                ), (
                    f"the field's annotation {resolver_annotation}"
                    f" does not match the origin annotation "
                    f"{self.origin.__annotations__[self.python_name]}"
                )
        elif not class_annotation:
            raise MissingReturnAnnotationError(self.python_name)

        else:
            self.origin.__annotations__[self.python_name] = (
                class_annotation or resolver_annotation.safe_resolve()
            )

        self.type_annotation = resolver_annotation or StrawberryAnnotation(
            class_annotation,
        )

        # fetching arguments
        self.arguments = self.base_resolver.arguments

        self._finalize()

    def _evaluate_as_basic_field(self) -> None:
        """Field without a resolver"""
        self.is_basic_field = True
        if self.default_factory is not UNSET:
            try:
                self.default_value = self.default_factory()
            except TypeError as exc:
                raise InvalidDefaultFactoryError() from exc

            self.default_value = self.default_factory()
        else:
            self.default_value = self.default

        module = sys.modules[self.origin.__module__]

        # Make sure the cls has an annotation
        if self.python_name not in self.origin.__annotations__:
            # If the field uses the default resolver, the field _must_ be
            # annotated
            raise MissingFieldAnnotationError(self.python_name)

        # fetch type annotation
        self.type_annotation = StrawberryAnnotation(
            annotation=self.origin.__annotations__[self.python_name],
            namespace=module.__dict__,
        )

        self._finalize()

    def _finalize(self) -> None:
        """Few validation after a field has been evaluated."""

        # Check that the field type is not Private
        if is_private(self.type):
            raise PrivateStrawberryFieldError(self.python_name, self.origin.__name__)

        # Check that default is not set if a resolver is defined
        if self.default is not UNSET and self.base_resolver is not None:
            raise FieldWithResolverAndDefaultValueError(
                self.python_name, self.origin.__name__
            )

        # Check that default_factory is not set if a resolver is defined
        if self.default_factory is not UNSET and self.base_resolver is not None:
            raise FieldWithResolverAndDefaultFactoryError(
                self.python_name, self.origin.__name__
            )

        assert_message = "Field must have a name by the time the schema is generated"
        assert self.python_name is not None, assert_message

    def to_dataclass_field(self) -> dataclasses.Field:
        # basic fields are fields with no provided resolver
        kw_only = {}
        if sys.version_info >= (3, 7):
            kw_only["kw_only"] = False

        default = dataclasses.MISSING
        default_factory = dataclasses.MISSING
        if self.is_basic_field:
            if self.default is not UNSET:
                default = self.default
            if self.default_factory is not UNSET:
                default_factory = self.default_factory
        field_ = dataclasses.Field(
            default=default,
            default_factory=(
                # mypy is not able to understand that default factory
                # is a callable, so we do a type ignore
                default_factory  # type: ignore
            ),
            init=self.is_basic_field,
            repr=self.is_basic_field,
            compare=self.is_basic_field,
            hash=None,
            metadata={},
            **kw_only,
        )

        field_.type = self.type_annotation.safe_resolve()
        return field_

    def get_result(
        self, _: Any, info: Info, args: List[Any], kwargs: Dict[str, Any]
    ) -> Union[Awaitable[Any], Any]:
        """
        Calls the resolver defined for the StrawberryField.
        If the field doesn't have a resolver defined we default
        to using the default resolver specified in StrawberryConfig.
        """

        if self.base_resolver:
            return self.base_resolver(*args, **kwargs)

        # else use default resolver
        return getattr(self.origin, self.python_name)  # type: ignore

    @property
    def type(self):
        # TODO: remove this property
        return self.type_annotation.safe_resolve()

    # TODO: add this to arguments (and/or move it to StrawberryType)
    @property
    def type_params(self) -> List[TypeVar]:
        if hasattr(self.type, "__strawberry_definition__"):
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
        if hasattr(self.type, "__strawberry_definition__"):
            type_definition: TypeDefinition = (
                self.type.__strawberry_definition__
            )  # type: ignore

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
    resolver: Callable[[], T],
    name: Optional[str] = None,
    is_subscription: bool = False,
    description: Optional[str] = None,
    init: Literal[False] = False,
    permission_classes: Optional[List[Type[BasePermission]]] = None,
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable, object] = UNSET,
    directives: Optional[Sequence[object]] = (),
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
    default: Any = UNSET,
    default_factory: Union[Callable, object] = UNSET,
    directives: Optional[Sequence[object]] = (),
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
    deprecation_reason: Optional[str] = None,
    default: Any = UNSET,
    default_factory: Union[Callable, object] = UNSET,
    directives: Optional[Sequence[object]] = (),
) -> StrawberryField:
    ...


def field(
    resolver=None,
    *,
    name=None,
    is_subscription=False,
    description=None,
    permission_classes=None,
    deprecation_reason=None,
    default=UNSET,
    default_factory=UNSET,
    directives=(),
    # This init parameter is used by PyRight to determine whether this field
    # is added in the constructor or not. It is not used to change
    # any behavior at the moment.
    init=None,
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
        base_resolver=resolver,
        is_subscription=is_subscription,
        description=description,
        permission_classes=permission_classes if permission_classes else [],
        deprecation_reason=deprecation_reason,
        directives=directives,
        default=default,
        default_factory=default_factory,
    )

    # if called like @strawberry.field or not as decorator but with field(resolver=...)
    if resolver:
        assert init is not True, "Can't set init as True when passing a resolver."
        field_(resolver)
        return field_

    # called like @strawberry.field(description="ABC") or not as decorator
    # further on the decorator would call StrawberryLazyField.__call__(decorated)
    else:
        return field_


__all__ = ["StrawberryField", "field"]
