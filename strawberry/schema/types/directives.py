import inspect
import typing
from itertools import islice

from strawberry.arguments import ArgumentDefinition, get_arguments_from_annotations


def get_arguments_for_directive(
    resolver: typing.Callable,
) -> typing.List[ArgumentDefinition]:
    # TODO: move this into directive declaration
    annotations = resolver.__annotations__
    annotations = dict(islice(annotations.items(), 1, None))
    annotations.pop("return", None)

    parameters = inspect.signature(resolver).parameters

    return get_arguments_from_annotations(annotations, parameters, origin=resolver)
