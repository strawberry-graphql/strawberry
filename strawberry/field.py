from typing import get_type_hints

from graphql import GraphQLField

from .constants import IS_STRAWBERRY_FIELD
from .type_converter import get_graphql_type_for_annotation
from .exceptions import MissingReturnAnnotationError


def field(wrap):
    setattr(wrap, IS_STRAWBERRY_FIELD, True)
    annotations = get_type_hints(wrap)

    name = wrap.__name__

    if "return" not in annotations:
        raise MissingReturnAnnotationError(name)

    field_type = get_graphql_type_for_annotation(annotations["return"], name)

    arguments_annotations = {
        key: value
        for key, value in annotations.items()
        if key not in ["info", "root", "return"]
    }

    arguments = {
        name: get_graphql_type_for_annotation(annotation, name)
        for name, annotation in arguments_annotations.items()
    }

    wrap.field = GraphQLField(field_type, args=arguments, resolve=wrap)
    return wrap
