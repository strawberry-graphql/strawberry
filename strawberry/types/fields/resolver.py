from __future__ import annotations as _

import builtins
import inspect
import sys
from inspect import isasyncgenfunction, iscoroutinefunction
from typing import Callable, Dict, Generic, List, Mapping, Optional, TypeVar, Union

from cached_property import cached_property  # type: ignore

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument
from strawberry.exceptions import MissingArgumentsAnnotationsError
from strawberry.type import StrawberryType
from strawberry.utils.inspect import get_func_args


T = TypeVar("T")


class StrawberryResolver(Generic[T]):
    # TODO: Move to StrawberryArgument? StrawberryResolver ClassVar?
    _SPECIAL_ARGS = {"root", "info", "self", "cls"}

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

    # TODO: Use this when doing the actual resolving? How to deal with async resolvers?
    def __call__(self, *args, **kwargs) -> T:
        if not callable(self.wrapped_func):
            raise UncallableResolverError(self)
        return self.wrapped_func(*args, **kwargs)

    @cached_property
    def annotations(self) -> Dict[str, object]:
        """Annotations for the resolver.

        Does not include special args defined in _SPECIAL_ARGS (e.g. self, root, info)
        """
        annotations = self._unbound_wrapped_func.__annotations__

        annotations = {
            name: annotation
            for name, annotation in annotations.items()
            if name not in self._SPECIAL_ARGS
        }

        return annotations

    @cached_property
    def arguments(self) -> List[StrawberryArgument]:
        parameters = inspect.signature(self._unbound_wrapped_func).parameters
        function_arguments = set(parameters) - self._SPECIAL_ARGS

        arguments = self.annotations.copy()
        arguments.pop("return", None)  # Discard return annotation to get just arguments

        arguments_missing_annotations = function_arguments - set(arguments)

        if any(arguments_missing_annotations):
            raise MissingArgumentsAnnotationsError(
                field_name=self.name,
                arguments=arguments_missing_annotations,
            )

        module = sys.modules[self._module]
        annotation_namespace = module.__dict__
        strawberry_arguments = []
        for arg_name, annotation in arguments.items():
            parameter = parameters[arg_name]

            argument = StrawberryArgument(
                python_name=arg_name,
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    annotation=annotation, namespace=annotation_namespace
                ),
                default=parameter.default,
            )

            strawberry_arguments.append(argument)

        return strawberry_arguments

    @cached_property
    def has_info_arg(self) -> bool:
        args = get_func_args(self._unbound_wrapped_func)
        return "info" in args

    @cached_property
    def has_root_arg(self) -> bool:
        args = get_func_args(self._unbound_wrapped_func)
        return "root" in args

    @cached_property
    def has_self_arg(self) -> bool:
        args = get_func_args(self._unbound_wrapped_func)
        return args and args[0] == "self"

    @cached_property
    def name(self) -> str:
        # TODO: What to do if resolver is a lambda?
        return self._unbound_wrapped_func.__name__

    @cached_property
    def type_annotation(self) -> Optional[StrawberryAnnotation]:
        try:
            return_annotation = self.annotations["return"]
        except KeyError:
            # No return annotation at all (as opposed to `-> None`)
            return None

        module = sys.modules[self._module]
        type_annotation = StrawberryAnnotation(
            annotation=return_annotation, namespace=module.__dict__
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
    def _module(self) -> str:
        return self._unbound_wrapped_func.__module__

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
