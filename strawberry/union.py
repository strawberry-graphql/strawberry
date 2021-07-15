import itertools
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Mapping,
    NoReturn,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from graphql import (
    GraphQLAbstractType,
    GraphQLNamedType,
    GraphQLResolveInfo,
    GraphQLType,
    GraphQLTypeResolver,
    GraphQLUnionType,
)

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    InvalidUnionType,
    UnallowedReturnTypeForUnion,
    WrongReturnTypeForUnion,
)
from strawberry.scalars import SCALAR_TYPES
from strawberry.type import StrawberryType


if TYPE_CHECKING:
    from strawberry.schema.types.concrete_type import TypeMap
    from strawberry.types.types import TypeDefinition


class StrawberryUnion(StrawberryType):
    def __init__(
        self,
        name: Optional[str] = None,
        type_annotations: Tuple["StrawberryAnnotation", ...] = tuple(),
        description: Optional[str] = None,
    ):
        self._name = name
        self.type_annotations = type_annotations
        self.description = description

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StrawberryType):
            if isinstance(other, StrawberryUnion):
                return (
                    self.name == other.name
                    and self.type_annotations == other.type_annotations
                    and self.description == other.description
                )
            return False

        return super().__eq__(other)

    def __hash__(self) -> int:
        # TODO: Is this a bad idea? __eq__ objects are supposed to have the same hash
        return id(self)

    @property
    def name(self) -> str:
        if self._name is not None:
            return self._name

        name = ""
        for type_ in self.types:
            if hasattr(type_, "_type_definition"):
                name += type_._type_definition.name  # type: ignore
            else:
                name += type.__name__

        return name

    @property
    def types(self) -> Tuple[StrawberryType, ...]:
        return tuple(
            cast(StrawberryType, annotation.resolve())
            for annotation in self.type_annotations
        )

    @property
    def type_params(self) -> List[TypeVar]:
        def _get_type_params(type_: StrawberryType):
            if hasattr(type_, "_type_definition"):
                parameters = getattr(type_, "__parameters__", None)

                return list(parameters) if parameters else []

            return type_.type_params

        # TODO: check if order is important:
        # https://github.com/strawberry-graphql/strawberry/issues/445
        return list(
            set(itertools.chain(*(_get_type_params(type_) for type_ in self.types)))
        )

    @property
    def is_generic(self) -> bool:
        return len(self.type_params) > 0

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> StrawberryType:
        if not self.is_generic:
            return self

        new_types = []
        for type_ in self.types:
            new_type: Union[StrawberryType, type]

            if hasattr(type_, "_type_definition"):
                type_definition: TypeDefinition = type_._type_definition  # type: ignore

                if type_definition.is_generic:
                    new_type = type_definition.copy_with(type_var_map)
            if isinstance(type_, StrawberryType) and type_.is_generic:
                new_type = type_.copy_with(type_var_map)
            else:
                new_type = type_

            new_types.append(new_type)

        return StrawberryUnion(
            type_annotations=tuple(map(StrawberryAnnotation, new_types)),
            description=self.description,
        )

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
        ) -> str:
            assert isinstance(type_, GraphQLUnionType)

            from strawberry.types.types import TypeDefinition

            # Make sure that the type that's passed in is an Object type
            if not hasattr(root, "_type_definition"):
                # TODO: If root=python dict, this won't work
                raise WrongReturnTypeForUnion(info.field_name, str(type(root)))

            return_type: Optional[GraphQLType]

            # Iterate over all of our known types and find the first concrete type that
            # implements the type
            for possible_concrete_type in type_map.values():
                possible_type = possible_concrete_type.definition
                if not isinstance(possible_type, TypeDefinition):
                    continue
                if possible_type.is_implemented_by(root):
                    return_type = possible_concrete_type.implementation
                    break
            else:
                return_type = None

            # Make sure the found type is expected by the Union
            if return_type is None or return_type not in type_.types:
                raise UnallowedReturnTypeForUnion(
                    info.field_name, str(type(root)), set(type_.types)
                )

            # Return the name of the type. Returning the actual type is now deprecated
            if isinstance(return_type, GraphQLNamedType):
                # TODO: Can return_type ever _not_ be a GraphQLNamedType?
                return return_type.name
            else:
                # todo: check if this is correct
                return return_type.__name__  # type: ignore

        return _resolve_union_type


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

    union_definition = StrawberryUnion(
        name=name,
        type_annotations=tuple(StrawberryAnnotation(type_) for type_ in types),
        description=description,
    )

    return union_definition
