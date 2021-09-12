from __future__ import annotations

import inspect
from typing import Any, Optional, Union

from typing_extensions import Annotated, get_args, get_origin

from strawberry.annotation import StrawberryAnnotation
from strawberry.type import StrawberryType
from strawberry.utils.mixins import GraphQLNameMixin

from ..exceptions import MultipleStrawberryArgumentsError


class _Unset:
    def __str__(self):
        return ""

    def __bool__(self):
        return False


UNSET: Any = _Unset()


def is_unset(value: Any) -> bool:
    # avoid multiple instances of this type
    return value is UNSET


class StrawberryArgumentAnnotation:
    description: Optional[str]
    name: Optional[str]

    def __init__(self, description: Optional[str] = None, name: Optional[str] = None):
        self.description = description
        self.name = name


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


__all__ = ["UNSET", "StrawberryArgumentAnnotation", "StrawberryArgument"]
