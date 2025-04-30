from __future__ import annotations as _

import asyncio
import inspect
import sys
import warnings
from functools import cached_property
from inspect import isasyncgenfunction
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    Generic,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
    cast,
)
from typing_extensions import Protocol, get_origin

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    ConflictingArgumentsError,
    MissingArgumentsAnnotationsError,
)
from strawberry.parent import StrawberryParent
from strawberry.types.arguments import StrawberryArgument
from strawberry.types.base import StrawberryType, has_object_definition
from strawberry.types.info import Info
from strawberry.utils.typing import type_has_annotation

if TYPE_CHECKING:
    import builtins
    from collections.abc import Mapping


class Parameter(inspect.Parameter):
    def __hash__(self) -> int:
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
        self,
        parameters: tuple[inspect.Parameter, ...],
        resolver: StrawberryResolver[Any],
    ) -> Optional[inspect.Parameter]:
        """Finds the reserved parameter from ``parameters``."""


class ReservedName(NamedTuple):
    name: str

    def find(
        self,
        parameters: tuple[inspect.Parameter, ...],
        resolver: StrawberryResolver[Any],
    ) -> Optional[inspect.Parameter]:
        del resolver
        return next((p for p in parameters if p.name == self.name), None)


class ReservedNameBoundParameter(NamedTuple):
    name: str

    def find(
        self,
        parameters: tuple[inspect.Parameter, ...],
        resolver: StrawberryResolver[Any],
    ) -> Optional[inspect.Parameter]:
        del resolver
        if parameters:  # Add compatibility for resolvers with no arguments
            first_parameter = parameters[0]
            return first_parameter if first_parameter.name == self.name else None
        return None


class ReservedType(NamedTuple):
    """Define a reserved type by name or by type.

    To preserve backwards-comaptibility, if an annotation was defined but does not match
    :attr:`type`, then the name is used as a fallback if available.
    """

    name: str | None
    type: type

    def find(
        self,
        parameters: tuple[inspect.Parameter, ...],
        resolver: StrawberryResolver[Any],
    ) -> Optional[inspect.Parameter]:
        # Go through all the types even after we've found one so we can
        # give a helpful error message if someone uses the type more than once.
        type_parameters = []
        for parameter in parameters:
            annotation = resolver.strawberry_annotations[parameter]
            if isinstance(annotation, StrawberryAnnotation):
                try:
                    evaled_annotation = annotation.evaluate()
                except NameError:
                    continue
                else:
                    if self.is_reserved_type(evaled_annotation):
                        type_parameters.append(parameter)

        if len(type_parameters) > 1:
            raise ConflictingArgumentsError(
                resolver, [parameter.name for parameter in type_parameters]
            )

        if type_parameters:
            return type_parameters[0]

        # Fallback to matching by name
        if not self.name:
            return None
        reserved_name = ReservedName(name=self.name).find(parameters, resolver)
        if reserved_name:
            warning = DeprecationWarning(
                f"Argument name-based matching of '{self.name}' is deprecated and will "
                "be removed in v1.0. Ensure that reserved arguments are annotated "
                "their respective types (i.e. use value: 'DirectiveValue[str]' instead "
                "of 'value: str' and 'info: Info' instead of a plain 'info')."
            )
            warnings.warn(warning, stacklevel=3)
            return reserved_name
        return None

    def is_reserved_type(self, other: builtins.type) -> bool:
        origin = cast(type, get_origin(other)) or other
        if origin is Annotated:
            # Handle annotated arguments such as Private[str] and DirectiveValue[str]
            return type_has_annotation(other, self.type)
        # Handle both concrete and generic types (i.e Info, and Info)
        return (
            issubclass(origin, self.type)
            if isinstance(origin, type)
            else origin is self.type
        )


SELF_PARAMSPEC = ReservedNameBoundParameter("self")
CLS_PARAMSPEC = ReservedNameBoundParameter("cls")
ROOT_PARAMSPEC = ReservedName("root")
INFO_PARAMSPEC = ReservedType("info", Info)
PARENT_PARAMSPEC = ReservedType(name=None, type=StrawberryParent)

T = TypeVar("T")

# in python >= 3.12 coroutine functions are market using inspect.markcoroutinefunction,
# which should be checked with inspect.iscoroutinefunction instead of asyncio.iscoroutinefunction
if hasattr(inspect, "markcoroutinefunction"):
    iscoroutinefunction = inspect.iscoroutinefunction
else:
    iscoroutinefunction = asyncio.iscoroutinefunction  # type: ignore[assignment]


class StrawberryResolver(Generic[T]):
    RESERVED_PARAMSPEC: tuple[ReservedParameterSpecification, ...] = (
        SELF_PARAMSPEC,
        CLS_PARAMSPEC,
        ROOT_PARAMSPEC,
        INFO_PARAMSPEC,
        PARENT_PARAMSPEC,
    )

    def __init__(
        self,
        func: Union[Callable[..., T], staticmethod, classmethod],
        *,
        description: Optional[str] = None,
        type_override: Optional[Union[StrawberryType, type]] = None,
    ) -> None:
        self.wrapped_func = func
        self._description = description
        self._type_override = type_override
        """Specify the type manually instead of calculating from wrapped func

        This is used when creating copies of types w/ generics
        """

    # TODO: Use this when doing the actual resolving? How to deal with async resolvers?
    def __call__(self, *args: str, **kwargs: Any) -> T:
        if not callable(self.wrapped_func):
            raise UncallableResolverError(self)
        return self.wrapped_func(*args, **kwargs)

    @cached_property
    def signature(self) -> inspect.Signature:
        return Signature.from_callable(self._unbound_wrapped_func, follow_wrapped=True)

    # TODO: find better name
    @cached_property
    def strawberry_annotations(
        self,
    ) -> dict[inspect.Parameter, Union[StrawberryAnnotation, None]]:
        return {
            p: (
                StrawberryAnnotation(p.annotation, namespace=self._namespace)
                if p.annotation is not inspect.Signature.empty
                else None
            )
            for p in self.signature.parameters.values()
        }

    @cached_property
    def reserved_parameters(
        self,
    ) -> dict[ReservedParameterSpecification, Optional[inspect.Parameter]]:
        """Mapping of reserved parameter specification to parameter."""
        parameters = tuple(self.signature.parameters.values())
        return {spec: spec.find(parameters, self) for spec in self.RESERVED_PARAMSPEC}

    @cached_property
    def arguments(self) -> list[StrawberryArgument]:
        """Resolver arguments exposed in the GraphQL Schema."""
        root_parameter = self.reserved_parameters.get(ROOT_PARAMSPEC)
        parent_parameter = self.reserved_parameters.get(PARENT_PARAMSPEC)

        # TODO: Maybe use SELF_PARAMSPEC in the future? Right now
        # it would prevent some common pattern for integrations
        # (e.g. django) of typing the `root` parameters as the
        # type of the real object being used
        if (
            root_parameter is not None
            and parent_parameter is not None
            and root_parameter.name != parent_parameter.name
        ):
            raise ConflictingArgumentsError(
                self,
                [root_parameter.name, parent_parameter.name],
            )

        parameters = self.signature.parameters.values()
        reserved_parameters = set(self.reserved_parameters.values())
        missing_annotations: list[str] = []
        arguments: list[StrawberryArgument] = []
        user_parameters = (p for p in parameters if p not in reserved_parameters)

        for param in user_parameters:
            annotation = self.strawberry_annotations[param]
            if annotation is None:
                missing_annotations.append(param.name)
            else:
                argument = StrawberryArgument(
                    python_name=param.name,
                    graphql_name=None,
                    type_annotation=annotation,
                    default=param.default,
                )
                arguments.append(argument)
        if missing_annotations:
            raise MissingArgumentsAnnotationsError(self, missing_annotations)
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
    def parent_parameter(self) -> Optional[inspect.Parameter]:
        return self.reserved_parameters.get(PARENT_PARAMSPEC)

    @cached_property
    def name(self) -> str:
        # TODO: What to do if resolver is a lambda?
        return self._unbound_wrapped_func.__name__

    # TODO: consider deprecating
    @cached_property
    def annotations(self) -> dict[str, object]:
        """Annotations for the resolver.

        Does not include special args defined in `RESERVED_PARAMSPEC` (e.g. self, root,
        info)
        """
        reserved_parameters = self.reserved_parameters
        reserved_names = {p.name for p in reserved_parameters.values() if p is not None}

        annotations = self._unbound_wrapped_func.__annotations__
        return {
            name: annotation
            for name, annotation in annotations.items()
            if name not in reserved_names
        }

    @cached_property
    def type_annotation(self) -> Optional[StrawberryAnnotation]:
        return_annotation = self.signature.return_annotation
        if return_annotation is inspect.Signature.empty:
            return None
        return StrawberryAnnotation(
            annotation=return_annotation, namespace=self._namespace
        )

    @property
    def type(self) -> Optional[Union[StrawberryType, type]]:
        if self._type_override:
            return self._type_override
        if self.type_annotation is None:
            return None
        return self.type_annotation.resolve()

    @property
    def is_graphql_generic(self) -> bool:
        from strawberry.schema.compat import is_graphql_generic

        has_generic_arguments = any(
            argument.is_graphql_generic for argument in self.arguments
        )

        return has_generic_arguments or bool(
            self.type and is_graphql_generic(self.type)
        )

    @cached_property
    def is_async(self) -> bool:
        return iscoroutinefunction(self._unbound_wrapped_func) or isasyncgenfunction(
            self._unbound_wrapped_func
        )

    def copy_with(
        self, type_var_map: Mapping[str, Union[StrawberryType, builtins.type]]
    ) -> StrawberryResolver:
        type_override = None

        if self.type:
            if isinstance(self.type, StrawberryType):
                type_override = self.type.copy_with(type_var_map)
            elif has_object_definition(self.type):
                type_override = self.type.__strawberry_definition__.copy_with(
                    type_var_map,
                )

        other = type(self)(
            func=self.wrapped_func,
            description=self._description,
            type_override=type_override,
        )
        # Resolve generic arguments
        for argument in other.arguments:
            if (
                isinstance(argument.type, StrawberryType)
                and argument.type.is_graphql_generic
            ):
                argument.type_annotation = StrawberryAnnotation(
                    annotation=argument.type.copy_with(type_var_map),
                    namespace=argument.type_annotation.namespace,
                )
        return other

    @cached_property
    def _namespace(self) -> dict[str, Any]:
        return sys.modules[self._unbound_wrapped_func.__module__].__dict__

    @cached_property
    def _unbound_wrapped_func(self) -> Callable[..., T]:
        if isinstance(self.wrapped_func, (staticmethod, classmethod)):
            return self.wrapped_func.__func__

        return self.wrapped_func


class UncallableResolverError(Exception):
    def __init__(self, resolver: StrawberryResolver) -> None:
        message = (
            f"Attempted to call resolver {resolver} with uncallable function "
            f"{resolver.wrapped_func}"
        )
        super().__init__(message)


__all__ = ["StrawberryResolver"]
