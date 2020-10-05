import typing

from graphql import GraphQLUnionType

from strawberry.exceptions import UnallowedReturnTypeForUnion, WrongReturnTypeForUnion
from strawberry.type import TypeDefinition
from strawberry.union import StrawberryUnion
from strawberry.utils.typing import (
    get_list_annotation,
    is_generic,
    is_list,
    is_type_var,
)

from .types import ConcreteType, TypeMap


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


def _find_type_for_generic_union(root: typing.Any) -> TypeDefinition:
    # this is a ordered tuple of the type vars for the generic class, so for
    # typing.Generic[T, V] it would return (T, V)
    type_params = root.__parameters__

    mapping = _get_type_mapping_from_actual_type(root)

    if not mapping:
        # if we weren't able to find a mapping, ie. when returning an empty list
        # for a generic type, then we fall back to returning the first copy.
        # This a very simplistic heuristic and it is bound to break with complex
        # uses cases. We can improve it later if this becomes an issue.

        return next((t for t in root._copies.values()))._type_definition

    types = tuple(mapping[param] for param in type_params)

    type = root._copies.get(types)

    if type is None:
        raise ValueError(f"Unable to find type for {root.__class__} and {types}")

    return type._type_definition


def get_union_type(
    union_definition: StrawberryUnion, type_map: TypeMap
) -> GraphQLUnionType:
    from .object_type import get_object_type

    def _resolve_type(root, info, _type):
        if not hasattr(root, "_type_definition"):
            raise WrongReturnTypeForUnion(info.field_name, str(type(root)))

        type_definition = root._type_definition

        if is_generic(type(root)):
            type_definition = _find_type_for_generic_union(root)

        returned_type = type_map[type_definition.name].implementation

        if returned_type not in _type.types:
            raise UnallowedReturnTypeForUnion(
                info.field_name, str(type(root)), _type.types
            )

        return returned_type

    types = union_definition.types

    if union_definition.name not in type_map:
        type_map[union_definition.name] = ConcreteType(
            definition=union_definition,
            implementation=GraphQLUnionType(
                union_definition.name,
                [get_object_type(type, type_map) for type in types],
                description=union_definition.description,
                resolve_type=_resolve_type,
            ),
        )

    return typing.cast(GraphQLUnionType, type_map[union_definition.name].implementation)
