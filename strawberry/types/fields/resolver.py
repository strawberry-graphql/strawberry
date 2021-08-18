from __future__ import annotations

import builtins
import inspect
import sys
from inspect import isasyncgenfunction, iscoroutinefunction
from typing import Any, Callable, Dict, Generic, Mapping, Optional, TypeVar, Union

from cached_property import cached_property  # type: ignore

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import UNSET
from strawberry.exceptions import MissingArgumentsAnnotationsError
from strawberry.type import StrawberryType
from strawberry.utils.inspect import get_func_args


T = TypeVar("T")


class StrawberryResolver(Generic[T]):
    def __init__(
        self,
        func: Callable[..., T],
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
        return self.wrapped_func(*args, **kwargs)

    @cached_property
    def function_parameters(self) -> Mapping[str, inspect.Parameter]:
        return inspect.signature(self.wrapped_func).parameters

    @cached_property
    def arguments(self) -> Dict[str, object]:
        # TODO: Move to StrawberryArgument? StrawberryResolver ClassVar?
        SPECIAL_ARGS = {"root", "self", "info"}

        annotations = self.wrapped_func.__annotations__
        parameters = self.function_parameters
        function_arguments = set(parameters) - SPECIAL_ARGS

        annotations = {
            name: annotation
            for name, annotation in annotations.items()
            if name not in (SPECIAL_ARGS | {"return"})
        }

        annotated_arguments = set(annotations)
        arguments_missing_annotations = function_arguments - annotated_arguments

        if any(arguments_missing_annotations):
            raise MissingArgumentsAnnotationsError(
                field_name=self.wrapped_func.__name__,
                arguments=arguments_missing_annotations,
            )

        return annotations

    @property
    def annotation_namespace(self):
        module = sys.modules[self.wrapped_func.__module__]
        annotation_namespace = module.__dict__

        return annotation_namespace

    def get_argument_default(self, arg_name: str) -> Any:
        func_parameters = self.function_parameters
        if arg_name not in func_parameters:
            return UNSET

        parameter = func_parameters[arg_name]
        return parameter.default

    @cached_property
    def has_info_arg(self) -> bool:
        args = get_func_args(self.wrapped_func)
        return "info" in args

    @cached_property
    def has_root_arg(self) -> bool:
        args = get_func_args(self.wrapped_func)
        return "root" in args

    @cached_property
    def has_self_arg(self) -> bool:
        args = get_func_args(self.wrapped_func)
        return args and args[0] == "self"

    @cached_property
    def name(self) -> str:
        # TODO: What to do if resolver is a lambda?
        return self.wrapped_func.__name__

    @cached_property
    def type_annotation(self) -> Optional[StrawberryAnnotation]:
        return_annotation = self.type
        if not return_annotation:
            return None

        annotation_namespace = self.annotation_namespace
        type_annotation = StrawberryAnnotation(
            annotation=return_annotation, namespace=annotation_namespace
        )

        return type_annotation

    @property
    def resolved_type(self) -> Optional[Union[StrawberryType, type]]:
        if self.type_annotation is None:
            return None
        return self.type_annotation.resolve()

    @property
    def type(self) -> Optional[Union[object, str]]:
        if self._type_override:
            return self._type_override
        try:
            return_annotation = self.wrapped_func.__annotations__["return"]
        except KeyError:
            # No return annotation at all (as opposed to `-> None`)
            return None

        return return_annotation

    @cached_property
    def is_async(self) -> bool:
        return iscoroutinefunction(self.wrapped_func) or isasyncgenfunction(
            self.wrapped_func
        )

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, builtins.type]]
    ) -> StrawberryResolver:
        type_override = None

        resolved_type = self.resolved_type
        if resolved_type:
            if isinstance(resolved_type, StrawberryType):
                type_override = resolved_type.copy_with(type_var_map)
            else:
                type_override = resolved_type._type_definition.copy_with(  # type: ignore
                    type_var_map,
                )

        return type(self)(
            func=self.wrapped_func,
            description=self._description,
            type_override=type_override,
        )


__all__ = ["StrawberryResolver"]
