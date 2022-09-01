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
    Optional,
    Sequence,
    Type,
    Union,
    cast,
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
from .types.fields.resolver import StrawberryResolver, resolveable


if TYPE_CHECKING:
    pass

_RESOLVER_TYPE = Union[StrawberryResolver, Callable, staticmethod, classmethod]

UNRESOLVED = object()


@dataclasses.dataclass()
class StrawberryField(StrawberryType):
    python_name: Optional[str] = None
    graphql_name: Optional[str] = None
    origin: Optional[Type] = None
    child: Optional["StrawberryField"] = None
    base_resolver: Optional[StrawberryResolver] = None
    type_annotation: Optional[StrawberryAnnotation] = None
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

    is_generic = False

    def __post_init__(self):
        if self.origin:
            assert (
                self.python_name
            ), "Python name must exist set when origin has been determined"
            if self.base_resolver:
                self._evaluate_from_base_resolver()

            else:
                self._evaluate_as_basic_field()
            if self.child:
                state = {
                    field_.name: field_
                    for field_ in dataclasses.fields(self)
                    if field_.init
                }
                state.pop("child")
                self.child = dataclasses.replace(self.child, **state)

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

        # if it is a StrawberryResolver
        if isinstance(evolvable, StrawberryResolver):
            return dataclasses.replace(self, base_resolver=evolvable)

        # if it is a type and not a resolver.
        elif inspect.isclass(evolvable):
            return dataclasses.replace(self, origin=evolvable)

        elif resolveable(evolvable):
            evolvable = StrawberryResolver(evolvable)

            return dataclasses.replace(self, base_resolver=evolvable)

        elif isinstance(evolvable, StrawberryField):
            new_type = type(
                self.__class__.__name__ + "_" + evolvable.__class__.__name__,
                (self.__class__, evolvable.__class__),
                {},
            )
            state = dataclasses.asdict(self)
            state.update(dataclasses.asdict(evolvable))
            new_type = cast(new_type, StrawberryField)
            return new_type(**state)

        else:
            raise TypeError(
                f"Unsupported type for field evolution, got: {type(evolvable)}"
            )

    @classmethod
    def from_dataclasses_field(
        cls, origin: Type, dataclasses_field: dataclasses.Field
    ) -> "StrawberryField":
        _default = UNSET
        _default_factory = UNSET
        if dataclasses_field.default is not dataclasses.MISSING:
            _default = dataclasses_field.default
        if (
            not _default
            and dataclasses_field.default_factory is not dataclasses.MISSING
        ):
            _default_factory = dataclasses_field.default_factory
        assert dataclasses_field.name
        return StrawberryField(
            origin=origin,
            default=_default,
            default_factory=_default_factory,
            python_name=dataclasses_field.name,
        )

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

        field_.type = self.type
        return field_

    # TODO: replace type with StrawberryObject
    def _evaluate_from_base_resolver(self) -> None:
        """
        called by __post_init__ if there is a base resolver and an origin.
        """
        # validate base_resolver
        if not isinstance(self.base_resolver, StrawberryResolver):
            if resolver := resolveable(self.base_resolver):
                self.base_resolver = StrawberryResolver(resolver)
            #     TODO: Tests this fails
            else:
                raise TypeError("Base resolver is not supported.")
        for argument in self.base_resolver.arguments:
            if isinstance(argument.type_annotation.annotation, str):
                continue
            elif isinstance(argument.type, StrawberryUnion):
                raise InvalidFieldArgument(
                    self.base_resolver.name,
                    argument.python_name,
                    "Union",
                )

            elif type_def := getattr(argument.type, "_type_definition", False):
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
            if namespace is not None:
                namespace.update(sys.modules[self.origin.__module__].__dict__)
            else:
                namespace = {}

            # check that class annotations if exists
            # are the same as resolver annotations.
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

        # no class or resolver annotation, raise exception.
        elif not class_annotation:
            raise MissingReturnAnnotationError(self.python_name)

        # only one annotation found, equalize!
        else:
            self.origin.__annotations__[self.python_name] = (
                class_annotation or resolver_annotation.safe_resolve()
            )

        self.type_annotation = resolver_annotation or StrawberryAnnotation(
            class_annotation,
        )
        # fetching arguments
        self.arguments = self.base_resolver.arguments

        # final checks.
        self._finalize()

    def _evaluate_as_basic_field(self) -> None:
        """Field without a resolver"""

        self.is_basic_field = True
        if self.default_factory is not UNSET:
            try:
                self.default_value = self.default_factory()
            except TypeError as exc:
                raise InvalidDefaultFactoryError() from exc
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

    @property
    def _has_async_permission_classes(self) -> bool:
        for permission_class in self.permission_classes:
            if inspect.iscoroutinefunction(permission_class.has_permission):
                return True
        return False

    @property
    def _has_async_base_resolver(self) -> bool:
        return self.base_resolver is not None and self.base_resolver.is_async

    def get_result(
        self, source: Any, info: Info, args: List[Any], kwargs: Dict[str, Any]
    ) -> Union[Awaitable[Any], Any]:
        """
        Calls the resolver defined for the StrawberryField.
        If the field doesn't have a resolver defined we default
        to using the default resolver specified in StrawberryConfig.
        """

        if self.base_resolver:
            res = self.base_resolver(*args, **kwargs)

        else:
            res = info.schema.config.default_resolver(
                source, self.python_name
            )  # type: ignore
        if self.child:
            res = self.child.get_result(res, info, args, kwargs)

        return res

    @cached_property
    def is_async(self) -> bool:
        return self._has_async_permission_classes or self._has_async_base_resolver

    @property
    def type(self):
        assert self.type_annotation
        return self.type_annotation.safe_resolve()

    def update_type_annotations(self, annotation: type):
        self.type_annotation = StrawberryAnnotation(annotation)

    @property
    def is_union(self) -> Optional[StrawberryUnion]:
        type_ = self.type
        if isinstance(type_, StrawberryUnion):
            return type_
        return None

    def validate(self, value):
        expected_type = self.type
        return super().base_validator(expected_type, value)


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
