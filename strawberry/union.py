from typing import TYPE_CHECKING, Any, Dict, NoReturn, Optional, Tuple, Type, TypeVar

from graphql import (
    GraphQLAbstractType,
    GraphQLResolveInfo,
    GraphQLTypeResolver,
    GraphQLUnionType,
)

from strawberry.exceptions import (
    InvalidUnionType,
    UnallowedReturnTypeForUnion,
    WrongReturnTypeForUnion,
)
from strawberry.scalars import SCALAR_TYPES
from strawberry.utils.typing import (
    get_list_annotation,
    is_generic,
    is_list,
    is_type_var,
)


if TYPE_CHECKING:
    from strawberry.schema.types.concrete_type import TypeMap
    from strawberry.types.types import TypeDefinition


class StrawberryUnion:
    def __init__(
        self, name: str, types: Tuple[Type, ...], description: Optional[str] = None
    ):
        self.name = name
        self._types = types
        self.description = description

    @property
    def types(self) -> Tuple[Type, ...]:
        from .types.type_resolver import _resolve_generic_type

        types = tuple(
            _resolve_generic_type(t, self.name)
            for t in self._types
            if t is not None.__class__
        )

        return types

    def __call__(self, *_args, **_kwargs) -> NoReturn:
        """Do not use.

        Used to bypass
        https://github.com/python/cpython/blob/5efb1a77e75648012f8b52960c8637fc296a5c6d/Lib/typing.py#L148-L149
        """
        raise ValueError("Cannot use union type directly")

    def get_type_resolver(self, type_map: "TypeMap") -> GraphQLTypeResolver:
        # TODO: Type annotate returned function

        def _resolve_union_type(
            root: Any, info: GraphQLResolveInfo, type_: GraphQLAbstractType
        ) -> Any:
            if not hasattr(root, "_type_definition"):
                raise WrongReturnTypeForUnion(info.field_name, str(type(root)))

            type_definition = root._type_definition

            if is_generic(type(root)):
                type_definition = self._find_type_for_generic_union(root)

            # TODO: There should be a way to do this without needing the TypeMap
            returned_type = type_map[type_definition.name].implementation

            assert isinstance(type_, GraphQLUnionType)  # For mypy
            if returned_type not in type_.types:
                raise UnallowedReturnTypeForUnion(
                    info.field_name, str(type(root)), set(type_.types)
                )

            return returned_type

        return _resolve_union_type

    def _find_type_for_generic_union(self, root: Any) -> "TypeDefinition":
        # this is a ordered tuple of the type vars for the generic class, so for
        # typing.Generic[T, V] it would return (T, V)
        type_params = root.__parameters__

        mapping = self._get_type_mapping_from_actual_type(root)

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

    def _get_type_mapping_from_actual_type(self, root) -> Dict[Any, Type]:
        # we map ~T to the actual type of root
        type_var_to_actual_type = {}

        for field_name, annotation in root.__annotations__.items():

            if is_list(annotation):
                # when we have a list we want to get the type of the elements
                # contained in the list, to do so we currently only get the first
                # time (if the list is not empty) this might break in more complex
                # cases, but should suffice for now.
                annotation = get_list_annotation(annotation)

                if is_type_var(annotation):
                    values = getattr(root, field_name)

                    if values:
                        type_var_to_actual_type[annotation] = type(values[0])

            elif is_type_var(annotation):
                type_var_to_actual_type[annotation] = type(getattr(root, field_name))

            elif is_generic(annotation):
                type_var_to_actual_type.update(
                    self._get_type_mapping_from_actual_type(getattr(root, field_name))
                )

        return type_var_to_actual_type


def union(
    name: str, types: Tuple[Type, ...], *, description: str = None
) -> StrawberryUnion:
    """Creates a new named Union type.

    Example usages:

    >>> @strawberry.type
    ... class A: ...
    >>> @strawberry.type
    ... class B: ...
    >>> strawberry.union("Name", (A, Optional[B]))
    """

    # Validate types
    if len(types) == 0:
        raise TypeError("No types passed to `union`")

    for _type in types:
        if _type in SCALAR_TYPES:
            raise InvalidUnionType(
                f"Scalar type `{_type.__name__}` cannot be used in a GraphQL Union"
            )

        if not isinstance(_type, TypeVar) and not hasattr(_type, "_type_definition"):
            raise InvalidUnionType(
                f"Union type `{_type.__name__}` is not a Strawberry type"
            )

    union_definition = StrawberryUnion(name=name, types=types, description=description)

    return union_definition
