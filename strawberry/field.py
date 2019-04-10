from typing import get_type_hints

from graphql import GraphQLField

from .constants import IS_STRAWBERRY_FIELD, IS_STRAWBERRY_INPUT
from .exceptions import MissingArgumentsAnnotationsError, MissingReturnAnnotationError
from .type_converter import get_graphql_type_for_annotation
from .utils.dict_to_type import dict_to_type
from .utils.inspect import get_func_args
from .utils.typing import (
    get_list_annotation,
    get_optional_annotation,
    is_list,
    is_optional,
)


def convert_args(args, annotations):
    """Converts a nested dictionary to a dictionary of strawberry input types."""

    converted_args = {}

    for key, value in args.items():
        annotation = annotations[key]

        # we don't need to check about unions here since they are not
        # yet supported for arguments.
        # see https://github.com/graphql/graphql-spec/issues/488

        is_list_of_args = False

        if is_optional(annotation):
            annotation = get_optional_annotation(annotation)

        if is_list(annotation):
            annotation = get_list_annotation(annotation)
            is_list_of_args = True

        if getattr(annotation, IS_STRAWBERRY_INPUT, False):
            if is_list_of_args:
                converted_args[key] = [dict_to_type(x, annotation) for x in value]
            else:
                converted_args[key] = dict_to_type(value, annotation)
        else:
            converted_args[key] = value

    return converted_args


def field(wrap, *, is_subscription=False):
    setattr(wrap, IS_STRAWBERRY_FIELD, True)
    annotations = get_type_hints(wrap)

    name = wrap.__name__

    if "return" not in annotations:
        raise MissingReturnAnnotationError(name)

    field_type = get_graphql_type_for_annotation(annotations["return"], name)

    function_arguments = set(get_func_args(wrap)) - {"self", "info"}

    arguments_annotations = {
        key: value
        for key, value in annotations.items()
        if key not in ["info", "return"]
    }

    annotated_function_arguments = set(arguments_annotations.keys())
    arguments_missing_annotations = function_arguments - annotated_function_arguments

    if len(arguments_missing_annotations) > 0:
        raise MissingArgumentsAnnotationsError(name, arguments_missing_annotations)

    arguments = {
        name: get_graphql_type_for_annotation(annotation, name)
        for name, annotation in arguments_annotations.items()
    }

    def resolver(source, info, **args):
        args = convert_args(args, arguments_annotations)

        return wrap(source, info, **args)

    if is_subscription:

        def _resolve(event, info):
            return event

        kwargs = {"subscribe": resolver, "resolve": _resolve}
    else:
        kwargs = {"resolve": resolver}

    wrap.field = GraphQLField(field_type, args=arguments, **kwargs)
    return wrap
