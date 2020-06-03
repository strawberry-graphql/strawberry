import typing

from graphql import GraphQLUnionType

from .exceptions import UnallowedReturnTypeForUnion, WrongReturnTypeForUnion
from .utils.typing import get_list_annotation, is_generic, is_list, is_type_var


def _get_type_mapping_from_actual_type(root) -> typing.Dict[typing.Any, typing.Type]:
    # we map ~T to the actual type of root
    type_var_to_actual_type = {}

    for field_name, annotation in root.__annotations__.items():
        # when we have a list we want to get the type of the elements contained in the
        # list, to do so we currently only get the first time (if the list is not empty)
        # this might break in more complex cases, but should suffice for now.

        if is_list(annotation):
            annotation = get_list_annotation(annotation)

            if is_type_var(annotation):
                values = getattr(root, field_name)

                if values:
                    type_var_to_actual_type[annotation] = type(values[0])

        elif is_type_var(annotation):
            type_var_to_actual_type[annotation] = type(getattr(root, field_name))

        elif is_generic(annotation):
            type_var_to_actual_type.update(
                _get_type_mapping_from_actual_type(getattr(root, field_name))
            )

    return type_var_to_actual_type


def _find_type_for_generic_union(root: typing.Any) -> typing.Type:
    # this is a ordered tuple of the type vars for the generic class, so for
    # typing.Generic[T, V] it would return (T, V)
    type_params = root.__parameters__

    mapping = _get_type_mapping_from_actual_type(root)

    if not mapping:
        # if we weren't able to find a mapping, ie. when returning an empty list
        # for a generic type, then we fall back to returning the first copy.
        # This a very simplistic heuristic and it is bound to break with complex
        # uses cases. We can improve it later if this becomes an issue.

        return next((t for t in root._copies.values()))

    types = tuple(mapping[param] for param in type_params)

    type = root._copies.get(types)

    if type is None:
        raise ValueError(f"Unable to find type for {root.__class__} and {types}")

    return type


def union(name: str, types: typing.Tuple[typing.Type], *, description=None):
    """Creates a new named Union type.

    Example usages:

    >>> strawberry.union(
    >>>     "Name",
    >>>     (A, B),
    >>> )

    >>> strawberry.union(
    >>>     "Name",
    >>>     (A, B),
    >>> )
    """

    from .type_converter import get_graphql_type_for_annotation

    def _resolve_type(root, info, _type):
        if not hasattr(root, "graphql_type"):
            raise WrongReturnTypeForUnion(info.field_name, str(type(root)))

        if is_generic(type(root)):
            return _find_type_for_generic_union(root)

        if root.graphql_type not in _type.types:
            raise UnallowedReturnTypeForUnion(
                info.field_name, str(type(root)), _type.types
            )

        return root.graphql_type

    # TODO: union types don't work with scalar types
    # so we want to return a nice error
    # also we want to make sure we have been passed
    # strawberry types
    graphql_type = GraphQLUnionType(
        name,
        [
            get_graphql_type_for_annotation(type, name, force_optional=True)
            for type in types
        ],
        description=description,
    )
    graphql_type.resolve_type = _resolve_type

    # This is currently a temporary solution, this is ok for now
    # But in future we might want to change this so that it works
    # properly with mypy, but there's no way to return a type like NewType does
    # so we return this class instance as it allows us to reuse the rest of
    # our code without doing too many changes

    class X:
        def __init__(self, graphql_type):
            self.graphql_type = graphql_type

    return X(graphql_type)
