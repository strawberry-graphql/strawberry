from __future__ import annotations

import dataclasses
import inspect
import sys
from typing import Any, Callable, List, Optional, Union

from typing_extensions import Annotated, get_args, get_origin

from strawberry.annotation import StrawberryAnnotation
from strawberry.type import StrawberryType
from strawberry.utils.mixins import GraphQLNameMixin

from ..exceptions import (
    MissingArgumentsAnnotationsError,
    MultipleStrawberryArgumentsError,
)


class _Unset:
    def __str__(self):
        return ""

    def __bool__(self):
        return False


UNSET: Any = _Unset()


def is_unset(value: Any) -> bool:
    # avoid multiple instances of this type
    return value is UNSET


@dataclasses.dataclass
class StrawberryArgumentAnnotation:
    description: Optional[str] = None
    name: Optional[str] = None


class StrawberryArgument(GraphQLNameMixin):
    def __init__(
        self,
        python_name: str,
        graphql_name: Optional[str],
        type_annotation: StrawberryAnnotation,
        is_subscription: bool = False,
        description: Optional[str] = None,
        default: object = UNSET,
    ) -> None:
        self.python_name = python_name  # type: ignore
        self.graphql_name = graphql_name
        self.is_subscription = is_subscription
        self.description = description
        self._type: Optional[StrawberryType] = None
        self.type_annotation = type_annotation

        # TODO: Consider moving this logic to a function
        self.default = UNSET if default is inspect.Parameter.empty else default

        if self._annotation_is_annotated(type_annotation):
            self._parse_annotated()

    @property
    def type(self) -> Union[StrawberryType, type]:
        return self.type_annotation.resolve()

    @classmethod
    def _annotation_is_annotated(cls, annotation: StrawberryAnnotation) -> bool:
        return get_origin(annotation.annotation) is Annotated

    def _parse_annotated(self):
        annotated_args = get_args(self.type_annotation.annotation)

        # The first argument to Annotated is always the underlying type
        self.type_annotation = StrawberryAnnotation(annotated_args[0])

        # Find any instances of StrawberryArgumentAnnotation
        # in the other Annotated args, raising an exception if there
        # are multiple StrawberryArgumentAnnotations
        argument_annotation_seen = False
        for arg in annotated_args[1:]:
            if isinstance(arg, StrawberryArgumentAnnotation):
                if argument_annotation_seen:
                    raise MultipleStrawberryArgumentsError(
                        argument_name=self.python_name
                    )

                argument_annotation_seen = True

                self.description = arg.description
                self.graphql_name = arg.name

    @classmethod
    def parse_from_func(cls, func: Callable) -> List[StrawberryArgument]:
        """Parse func arguments as strawberry arguments.

        Intended to be used with a resolver func"""
        # TODO: Do we want this to be a private function?
        SPECIAL_ARGS = {"root", "self", "info"}

        annotations = func.__annotations__
        parameters = inspect.signature(func).parameters
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
                field_name=func.__name__,
                arguments=arguments_missing_annotations,
            )

        module = sys.modules[func.__module__]
        annotation_namespace = module.__dict__
        arguments = []
        for arg_name, annotation in annotations.items():
            parameter = parameters[arg_name]

            argument = StrawberryArgument(
                python_name=arg_name,
                graphql_name=None,
                type_annotation=StrawberryAnnotation(
                    annotation=annotation, namespace=annotation_namespace
                ),
                default=parameter.default,
            )

            arguments.append(argument)

        return arguments


__all__ = ["UNSET", "StrawberryArgumentAnnotation", "StrawberryArgument"]
