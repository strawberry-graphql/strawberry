import inspect
from inspect import isasyncgenfunction, iscoroutinefunction
from typing import Callable, Generic, List, Optional, Type, TypeVar

from cached_property import cached_property  # type: ignore

from strawberry.arguments import StrawberryArgument, get_arguments_from_annotations
from strawberry.exceptions import MissingArgumentsAnnotationsError
from strawberry.utils.inspect import get_func_args


T = TypeVar("T")


class StrawberryResolver(Generic[T]):
    def __init__(self, func: Callable[..., T], *, description: Optional[str] = None):
        self.wrapped_func = func
        self._description = description

    # TODO: Use this when doing the actual resolving? How to deal with async resolvers?
    def __call__(self, *args, **kwargs) -> T:
        return self.wrapped_func(*args, **kwargs)

    @cached_property
    def arguments(self) -> List[StrawberryArgument]:
        # TODO: Move to StrawberryArgument? StrawberryResolver ClassVar?
        SPECIAL_ARGS = {"root", "self", "info"}

        annotations = self.wrapped_func.__annotations__
        parameters = inspect.signature(self.wrapped_func).parameters
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

        return get_arguments_from_annotations(
            annotations, parameters, origin=self.wrapped_func
        )

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
    def type(self) -> Type[T]:
        return self.wrapped_func.__annotations__.get("return", None)

    @cached_property
    def is_async(self) -> bool:
        return iscoroutinefunction(self.wrapped_func) or isasyncgenfunction(
            self.wrapped_func
        )


__all__ = ["StrawberryResolver"]
