from __future__ import annotations as _

import builtins
import inspect
import sys
import warnings
from inspect import isasyncgenfunction, iscoroutinefunction
from typing import (  # type: ignore[attr-defined]
    Any,
    Callable,
    Dict,
    ForwardRef,
    Generic,
    List,
    Mapping,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    _eval_type,
)

from backports.cached_property import cached_property
from typing_extensions import Annotated, Protocol, get_args, get_origin

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.exceptions import MissingArgumentsAnnotationsError
from strawberry.type import StrawberryType
from strawberry.types.info import Info


class Parameter(inspect.Parameter):
    def __hash__(self):
        """Override to exclude default value from hash.

        This adds compatibility for using unhashable default values in resolvers such as
        list and dict. The present use-case is limited to analyzing parameters from one
        resolver. Therefore, the name, kind, and annotation combination are guaranteed
        to be unique since two arguments cannot have the same name in a callable.

        Furthermore, even though it is not currently a use-case to collect parameters
        from different resolvers, the likelihood of collision from having the same hash
        value but different defaults is mitigated by Python invoking the
        :py:meth:`__eq__` method if two items have the same hash. See the verification
        of this behavior in the `test_parameter_hash_collision` test.
        """
        return hash((self.name, self.kind, self.annotation))


class Signature(inspect.Signature):

    _parameter_cls = Parameter


class ReservedParameterSpecification(Protocol):
    def find(
        self, parameters: Tuple[inspect.Parameter, ...], resolver: StrawberryResolver
    ) -> Optional[inspect.Parameter]:
        """Finds the reserved parameter from ``parameters``."""


class ReservedName(NamedTuple):
    name: str

    def find(
        self, parameters: Tuple[inspect.Parameter, ...], _: StrawberryResolver
    ) -> Optional[inspect.Parameter]:
        return next((p for p in parameters if p.name == self.name), None)


class ReservedNameBoundParameter(NamedTuple):
    name: str

    def find(
        self, parameters: Tuple[inspect.Parameter, ...], _: StrawberryResolver
    ) -> Optional[inspect.Parameter]:
        if parameters:  # Add compatibility for resolvers with no arguments
            first_parameter = parameters[0]
            return first_parameter if first_parameter.name == self.name else None
        else:
            return None


class ReservedType(NamedTuple):
    """Define a reserved type by name or by type.

    To preserve backwards-comaptibility, if an annotation was defined but does not match
    :attr:`type`, then the name is used as a fallback.
    """

    name: str
    type: Type

    def find(
        self, parameters: Tuple[inspect.Parameter, ...], resolver: StrawberryResolver
    ) -> Optional[inspect.Parameter]:
        for parameter in parameters:
            annotation = parameter.annotation
            try:
                resolved_annotation = _eval_type(
                    ForwardRef(annotation)
                    if isinstance(annotation, str)
                    else annotation,
                    resolver._namespace,
                    None,
                )
                resolver._resolved_annotations[parameter] = resolved_annotation
            except NameError:
                # Type-annotation could not be resolved
                resolved_annotation = annotation
            if self.is_reserved_type(resolved_annotation):
                return parameter

        # Fallback to matching by name
        reserved_name = ReservedName(name=self.name).find(parameters, resolver)
        if reserved_name:
            warning = DeprecationWarning(
                f"Argument name-based matching of '{self.name}' is deprecated and will "
                "be removed in v1.0. Ensure that reserved arguments are annotated "
                "their respective types (i.e. use value: 'DirectiveValue[str]' instead "
                "of 'value: str' and 'info: Info' instead of a plain 'info')."
            )
            warnings.warn(warning)
            return reserved_name
        else:
            return None

    def is_reserved_type(self, other: Type) -> bool:
        if get_origin(other) is Annotated:
            # Handle annotated arguments such as Private[str] and DirectiveValue[str]
            return any(isinstance(argument, self.type) for argument in get_args(other))
        else:
            # Handle both concrete and generic types (i.e Info, and Info[Any, Any])
            return other is self.type or get_origin(other) is self.type


SELF_PARAMSPEC = ReservedNameBoundParameter("self")
CLS_PARAMSPEC = ReservedNameBoundParameter("cls")
ROOT_PARAMSPEC = ReservedName("root")
INFO_PARAMSPEC = ReservedType("info", Info)

T = TypeVar("T")


class StrawberryResolver(Generic[T]):

    RESERVED_PARAMSPEC: Tuple[ReservedParameterSpecification, ...] = (
        SELF_PARAMSPEC,
        CLS_PARAMSPEC,
        ROOT_PARAMSPEC,
        INFO_PARAMSPEC,
    )

    def __init__(
        self,
        func: Union[Callable[..., T], staticmethod, classmethod],
        *,
        description: Optional[str] = None,
        type_override: Optional[Union[StrawberryType, type]] = None,
    ):
        self.wrapped_func = func
        self._description = description
        self._type_override = type_override
        """Specify the type manually instead of calculating from wrapped func

        This is used when creating copies of types w/ generics
        """
        self._resolved_annotations: Dict[inspect.Parameter, Any] = {}
        """Populated during reserved parameter determination.

        Caching resolved annotations this way prevents evaling them repeatedly.
        """

    # TODO: Use this when doing the actual resolving? How to deal with async resolvers?
    def __call__(self, *args, **kwargs) -> T:
        if not callable(self.wrapped_func):
            raise UncallableResolverError(self)
        return self.wrapped_func(*args, **kwargs)

    @cached_property
    def signature(self) -> inspect.Signature:
        return Signature.from_callable(self._unbound_wrapped_func, follow_wrapped=True)

    @cached_property
    def reserved_parameters(
        self,
    ) -> Dict[ReservedParameterSpecification, Optional[inspect.Parameter]]:
        """Mapping of reserved parameter specification to parameter."""
        parameters = tuple(self.signature.parameters.values())
        return {spec: spec.find(parameters, self) for spec in self.RESERVED_PARAMSPEC}

    @cached_property
    def arguments(self) -> List[StrawberryArgument]:
        """Resolver arguments exposed in the GraphQL Schema."""
        parameters = self.signature.parameters.values()
        reserved_parameters = set(self.reserved_parameters.values())

        missing_annotations = set()
        arguments = []
        user_parameters = (p for p in parameters if p not in reserved_parameters)
        for param in user_parameters:
            annotation = self._resolved_annotations.get(param, param.annotation)
            if annotation is inspect.Signature.empty:
                missing_annotations.add(param.name)
            else:
                argument = StrawberryArgument(
                    python_name=param.name,
                    graphql_name=None,
                    type_annotation=StrawberryAnnotation(
                        annotation=annotation, namespace=self._namespace
                    ),
                    default=param.default,
                )
                arguments.append(argument)
        if missing_annotations:
            raise MissingArgumentsAnnotationsError(self.name, missing_annotations)
        return arguments

    @cached_property
    def info_parameter(self) -> Optional[inspect.Parameter]:
        return self.reserved_parameters.get(INFO_PARAMSPEC)

    @cached_property
    def root_parameter(self) -> Optional[inspect.Parameter]:
        return self.reserved_parameters.get(ROOT_PARAMSPEC)

    @cached_property
    def self_parameter(self) -> Optional[inspect.Parameter]:
        return self.reserved_parameters.get(SELF_PARAMSPEC)

    @cached_property
    def name(self) -> str:
        # TODO: What to do if resolver is a lambda?
        return self._unbound_wrapped_func.__name__

    @cached_property
    def annotations(self) -> Dict[str, object]:
        """Annotations for the resolver.

        Does not include special args defined in `RESERVED_PARAMSPEC` (e.g. self, root,
        info)
        """
        reserved_parameters = self.reserved_parameters
        reserved_names = {p.name for p in reserved_parameters.values() if p is not None}

        annotations = self._unbound_wrapped_func.__annotations__
        annotations = {
            name: annotation
            for name, annotation in annotations.items()
            if name not in reserved_names
        }

        return annotations

    @cached_property
    def type_annotation(self) -> Optional[StrawberryAnnotation]:
        return_annotation = self.signature.return_annotation
        if return_annotation is inspect.Signature.empty:
            return None
        else:
            type_annotation = StrawberryAnnotation(
                annotation=return_annotation, namespace=self._namespace
            )
        return type_annotation

    @property
    def type(self) -> Optional[Union[StrawberryType, type]]:
        if self._type_override:
            return self._type_override
        if self.type_annotation is None:
            return None
        return self.type_annotation.resolve()

    @cached_property
    def is_async(self) -> bool:
        return iscoroutinefunction(self._unbound_wrapped_func) or isasyncgenfunction(
            self._unbound_wrapped_func
        )

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, builtins.type]]
    ) -> StrawberryResolver:
        type_override = None

        if self.type:
            if isinstance(self.type, StrawberryType):
                type_override = self.type.copy_with(type_var_map)
            else:
                type_override = self.type._type_definition.copy_with(  # type: ignore
                    type_var_map,
                )

        return type(self)(
            func=self.wrapped_func,
            description=self._description,
            type_override=type_override,
        )

    @cached_property
    def _namespace(self) -> Dict[str, Any]:
        return sys.modules[self._unbound_wrapped_func.__module__].__dict__

    @cached_property
    def _unbound_wrapped_func(self) -> Callable[..., T]:
        if isinstance(self.wrapped_func, (staticmethod, classmethod)):
            return self.wrapped_func.__func__

        return self.wrapped_func


class UncallableResolverError(Exception):
    def __init__(self, resolver: "StrawberryResolver"):
        message = (
            f"Attempted to call resolver {resolver} with uncallable function "
            f"{resolver.wrapped_func}"
        )
        super().__init__(message)


__all__ = ["StrawberryResolver"]
