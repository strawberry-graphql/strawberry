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
from typing_extensions import Literal

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.exceptions import (
    FieldWithResolverAndDefaultFactoryError,
    FieldWithResolverAndDefaultValueError,
    InvalidFieldArgument,
    MissingFieldAnnotationError,
    MissingReturnAnnotationError,
    PrivateStrawberryFieldError,
)
from strawberry.type import StrawberryType, StrawberryTypeVar
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


@dataclasses.dataclass(frozen=True)
class DataclassFieldSettings:
    default: object = UNSET
    default_factory: Union[Callable[[], Any], object] = UNSET
    if sys.version_info >= (3, 10):
        kw_only: bool = False
    kwargs: dict = dataclasses.field(default_factory=lambda: {})
    """
    additional kwargs to be passed to dataclasses.Field.
    !WARNING: strawberry is not responsible for any kwargs you have passed to
    dataclass, strawberry is only tested against the provided arguments.
    """
    is_basic_field: bool = False
    """
    basic fields are fields with no provided resolver.
    if true it would be used as a plain dataclass field.
    """

    @classmethod
    def create(
        cls,
        default: object = UNSET,
        default_factory: Union[Callable[[], Any], object] = UNSET,
        is_basic_field: bool = False,
        kwargs: dict = None,
    ) -> "DataclassFieldSettings":
        return cls(
            default,
            default_factory,
            is_basic_field=is_basic_field,
            kwargs=kwargs if kwargs else {},
        )

    def to_dataclass_field(self) -> dataclasses.Field:
        kwargs = dataclasses.asdict(self)
        kwargs.update(kwargs.pop("kwargs"))
        # basic fields are fields with no provided resolver
        default = dataclasses.MISSING
        default_factory = dataclasses.MISSING
        if not self.is_basic_field:
            if self.default is not UNSET:
                default = self.default
            if self.default_factory is not UNSET:
                default_factory = self.default_factory
        return dataclasses.Field(
            default=default,
            default_factory=(
                # mypy is not able to understand that default factory
                # is a callable so we do a type ignore
                default_factory  # type: ignore
            ),
            init=self.is_basic_field,
            repr=self.is_basic_field,
            compare=self.is_basic_field,
            hash=None,
            metadata={},
            **kwargs,
        )


DEFAULT_FIELD_SETTINGS = DataclassFieldSettings()


@dataclasses.dataclass(frozen=True)
class StrawberryField:
    python_name: Optional[str]
    """
    name to be used by python, i.e in the generated __init__
    """
    graphql_name: Optional[str]
    """
    name to be used by graphql queries, mutations, etc...
    """
    type_annotation: Union[StrawberryAnnotation, type] = None
    """
    the return type of this field
    """
    origin: Optional[Union[Type, Callable, staticmethod, classmethod]] = None
    """
    the strawberry.type class that this resolver lives in.
    """
    base_resolver: Optional[StrawberryResolver] = None
    """
    non-default resolver. if exists, it will be used rather
    then the default dataclass field value.
    """
    arguments: List[StrawberryArgument] = dataclasses.field(default_factory=list)
    """
    the field's resolver, will be used by `get_result`.
    """
    is_subscription: bool = False
    description: Optional[str] = None
    """
    to be used in the schema docs.
    """
    deprecation_reason: Optional[str] = None
    permission_classes: List[Type[BasePermission]] = dataclasses.field(
        default_factory=list
    )
    directives: Sequence[object] = ()
    dataclass_options: Optional[DataclassFieldSettings] = DEFAULT_FIELD_SETTINGS
    is_basic_field: bool = False

    def __post_init__(self):
        # any errors due to invalid implementation
        # should be reported here,
        # because any evolve / dataclasses.replace will call __post_init__.
        if isinstance(self.base_resolver, StrawberryResolver):
            for argument in self.base_resolver.arguments:
                if isinstance(argument.type_annotation.annotation, str):
                    continue
                elif isinstance(argument.type, StrawberryUnion):
                    raise InvalidFieldArgument(
                        self.base_resolver.name,
                        argument.python_name,
                        "Union",
                    )

                elif getattr(argument.type, "_type_definition", False):
                    if argument.type._type_definition.is_interface:  # type: ignore
                        raise InvalidFieldArgument(
                            self.base_resolver.name,
                            argument.python_name,
                            "Interface",
                        )
        # checks that only applied after origin has been determined.
        # this would normally be checked after StrawberryField.evolve has been called.
        if self.origin:
            # Check that the field type is not Private
            if is_private(self.type_annotation.resolve()):
                raise PrivateStrawberryFieldError(
                    self.python_name, self.origin.__name__
                )
            # Check that default is not set if a resolver is defined
            if (
                self.dataclass_options.default is not UNSET
                and self.base_resolver is not None
            ):
                raise FieldWithResolverAndDefaultValueError(
                    self.python_name, self.origin.__name__
                )
            # Check that default_factory is not set if a resolver is defined
            # Note: using getattr because of this issue:
            # https://github.com/python/mypy/issues/6910
            if (
                self.dataclass_options.default_factory is not UNSET  # noqa
                and self.base_resolver is not None
            ):
                raise FieldWithResolverAndDefaultFactoryError(
                    self.python_name, self.origin.__name__
                )

            assert_message = (
                "Field must have a name by the time the schema is generated"
            )
            assert self.python_name is not None, assert_message

    @classmethod
    def create(
        cls,
        python_name: Optional[str] = None,
        graphql_name: Optional[str] = None,
        type_annotation: Optional[Union[StrawberryAnnotation, type]] = None,
        origin: Optional[Union[Type, Callable, staticmethod, classmethod]] = None,
        base_resolver: Optional[StrawberryResolver] = None,
        is_subscription: bool = False,
        description: Optional[str] = None,
        deprecation_reason: Optional[str] = None,
        permission_classes=None,  # type: ignore
        directives: Sequence[object] = (),
        dataclass_options: Optional[DataclassFieldSettings] = DEFAULT_FIELD_SETTINGS,
        is_basic_field: bool = False,
        # legacy compatibility, will be passed to dataclass_options:
        default: object = UNSET,
        default_factory: Union[Callable[[], Any], object] = UNSET,
    ) -> "StrawberryField":
        """
        This is a base method,
        it will be used by either from_resolver or from_basic_field.
        users can override this, to provide custom logic for creating the type.
        it will be called by `strawberry.type`
        """
        if permission_classes is None:
            permission_classes = []

        if default or default_factory:
            dataclass_options = DataclassFieldSettings(
                default=default,
                default_factory=default_factory,
                is_basic_field=is_basic_field,
            )
        type_annotation
        return cls(
            python_name=python_name,
            graphql_name=graphql_name or python_name,
            type_annotation=type_annotation,
            origin=origin,
            is_subscription=is_subscription,
            description=description,
            deprecation_reason=deprecation_reason,
            base_resolver=base_resolver,
            permission_classes=permission_classes,
            directives=directives,
            dataclass_options=dataclass_options,
            is_basic_field=is_basic_field,
        )

    @classmethod
    def evolve_with_resolver(
        cls,
        instance: "StrawberryField",
        base_resolver: StrawberryResolver,
        origin: Union[Type, Callable, staticmethod, classmethod],
    ) -> "StrawberryField":

        python_name = base_resolver.name

        if base_resolver.type_annotation is None:
            raise MissingReturnAnnotationError(python_name)

        type_annotation = base_resolver.type_annotation
        if annotated := origin.__annotations__.get(python_name):
            assert annotated == type_annotation, (
                f"the field's annotation {type_annotation}"
                f" does not match the origin annotation "
                f"{origin.__annotations__[python_name]}"
            )

        origin.__annotations__[python_name] = type_annotation
        return dataclasses.replace(
            instance,
            origin=origin,
            python_name=python_name,
            type_annotation=type_annotation,
            arguments=base_resolver.arguments,
        )

    @classmethod
    def evolve_with_basic_field(
        cls,
        instance: "StrawberryField",
        origin: Union[Type, Callable, staticmethod, classmethod],
        python_name: str,
    ) -> "StrawberryField":
        """Field without a resolver"""

        # Make sure the cls has an annotation
        if python_name not in origin.__annotations__:
            # If the field uses the default resolver, the field _must_ be
            # annotated
            raise MissingFieldAnnotationError(python_name)
        return dataclasses.replace(
            instance, origin=origin, python_name=python_name, is_basic_field=True
        )

    def to_dataclass_field(self) -> dataclasses.Field:
        return self.dataclass_options.to_dataclass_field()

    def get_result(
        self, source: Any, info: Info, args: List[Any], kwargs: Dict[str, Any]
    ) -> Union[Awaitable[Any], Any]:
        """
        Calls the resolver defined for the StrawberryField.
        If the field doesn't have a resolver defined we default
        to using the default resolver specified in StrawberryConfig.
        """

        if self.base_resolver:
            return self.base_resolver(*args, **kwargs)

        return getattr(source, self.python_name)  # type: ignore

    @classmethod
    def resolve_type(
        cls, instance: "StrawberryField", strawberry_type: Type
    ) -> "StrawberryField":
        # try to get type from resolver.
        if (
            instance.base_resolver is not None
            and instance.base_resolver.type is not None
            and not isinstance(instance.base_resolver.type, StrawberryTypeVar)
        ):
            res = instance.base_resolver.type

        # if we got a StrawberryAnnotation instead of plain type.
        elif isinstance(instance.type_annotation, StrawberryAnnotation):
            res = instance.type_annotation.resolve()

        # resolve from the class this field is defined in.
        else:
            if not (
                res := getattr(
                    strawberry_type, "__annotations__", {instance.python_name: False}
                )[instance.python_name]
            ):
                raise Exception(
                    f"Could not resolve type annotation for field: {instance}"
                )

        return dataclasses.replace(instance, type_annotation=res)

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


T = TypeVar("T")


class StrawberryLazyField:
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

    def __init__(self, pre_processed_field: StrawberryField):
        self.pre_processed_field = pre_processed_field
        self.resolver: Union[Callable[..., T], staticmethod, classmethod] = None

    def __call__(
        self, resolver: Union[Callable[..., T], staticmethod, classmethod]
    ) -> None:
        """
        hack for decorators
        """
        self.resolver = resolver

    def evaluate(self, origin: Type, field_name: str) -> StrawberryField:
        if resolver := self.resolver or self.pre_processed_field.base_resolver:
            if not isinstance(resolver, StrawberryResolver):
                resolver = StrawberryResolver(resolver)

            return StrawberryField.evolve_with_resolver(
                self.pre_processed_field, resolver, origin
            )
        else:
            return StrawberryField.evolve_with_basic_field(
                self.pre_processed_field, origin, field_name
            )


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
) -> StrawberryLazyField:
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

    field_ = StrawberryLazyField(
        StrawberryField.create(
            python_name=name,
            is_subscription=is_subscription,
            description=description,
            permission_classes=permission_classes,
            deprecation_reason=deprecation_reason,
            default=default,
            default_factory=default_factory,
            directives=directives,
        )
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
