from __future__ import annotations

import dataclasses
import inspect
import sys
from itertools import islice
from typing import Callable, List, Optional, TypeVar

from graphql import DirectiveLocation

from strawberry.annotation import StrawberryAnnotation
from strawberry.arguments import StrawberryArgument


@dataclasses.dataclass
class StrawberryDirective:
    python_name: str
    graphql_name: Optional[str]
    resolver: Callable
    locations: List[DirectiveLocation]
    description: Optional[str] = None

    @property
    def arguments(self) -> List[StrawberryArgument]:
        annotations = self.resolver.__annotations__
        annotations = dict(islice(annotations.items(), 1, None))
        annotations.pop("return", None)

        parameters = inspect.signature(self.resolver).parameters

        module = sys.modules[self.resolver.__module__]
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


T = TypeVar("T")


def directive(
    *,
    locations: List[DirectiveLocation],
    description: Optional[str] = None,
    name: Optional[str] = None
) -> Callable[[Callable[..., T]], T]:
    def _wrap(f: Callable[..., T]) -> T:
        return StrawberryDirective(  # type: ignore
            python_name=f.__name__,
            graphql_name=name,
            locations=locations,
            description=description,
            resolver=f,
        )

    return _wrap


__all__ = ["DirectiveLocation", "StrawberryDirective", "directive"]
