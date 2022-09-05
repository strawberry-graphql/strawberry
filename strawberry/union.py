from typing import (
    TYPE_CHECKING,
    Any,
    Iterable,
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
from strawberry.type import StrawberryOptional, StrawberryType


if TYPE_CHECKING:
    from strawberry.schema.types.concrete_type import TypeMap


class StrawberryUnion(StrawberryType):
    def __init__(
        self,
        name: Optional[str] = None,
        type_annotations: Tuple["StrawberryAnnotation", ...] = tuple(),
        description: Optional[str] = None,
        directives: Iterable[object] = (),
    ):
        self.graphql_name = name
        self.type_annotations = type_annotations
        self.description = description
        self.directives = directives

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StrawberryType):
            if isinstance(other, StrawberryUnion):
                return (
                    self.graphql_name == other.graphql_name
                    and self.type_annotations == other.type_annotations
                    and self.description == other.description
                )
            return False

        return super().__eq__(other)

    def __hash__(self) -> int:
        # TODO: Is this a bad idea? __eq__ objects are supposed to have the same hash
        return id(self)

    def __or__(self, other: Union[StrawberryType, type]) -> StrawberryType:
        if other is None:
            # Return the correct notation when using `StrawberryUnion | None`.
            return StrawberryOptional(of_type=self)

        # Raise an error in any other case.
        # There is Work in progress to deal with more merging cases, see:
        # https://github.com/strawberry-graphql/strawberry/pull/1455
        raise InvalidUnionType(other)

    @property
    def types(self) -> Tuple[StrawberryType, ...]:
        return tuple(
            cast(StrawberryType, annotation.resolve())
            for annotation in self.type_annotations
        )

    @property
    def is_generic(self) -> bool:
        return False

    def __call__(self, *_args, **_kwargs) -> NoReturn:
        """Do not use.

        Used to bypass
        https://github.com/python/cpython/blob/5efb1a77e75648012f8b52960c8637fc296a5c6d/Lib/typing.py#L148-L149
        """
        raise ValueError("Cannot use union type directly")

    def get_type_resolver(self, type_map: "TypeMap") -> GraphQLTypeResolver:
        def _resolve_union_type(
            root: Any, info: GraphQLResolveInfo, type_: GraphQLAbstractType
        ) -> str:
            assert isinstance(type_, GraphQLUnionType)

            from strawberry.types.types import get_type_definition

            # If the type given is not an Object type, try resolving using `is_type_of`
            # defined on the union's inner types
            if not hasattr(root, "_type_definition"):
                for inner_type in type_.types:
                    if inner_type.is_type_of is not None and inner_type.is_type_of(
                        root, info
                    ):
                        return inner_type.name

                # Couldn't resolve using `is_type_of`
                raise WrongReturnTypeForUnion(info.field_name, str(type(root)))

            return_type: Optional[GraphQLType] = None

            if root_definition := get_type_definition(root):
                if template := root_definition.is_generic:
                    for _, implementation in template.implementations.items():
                        if implementation := get_type_definition(implementation):
                            if implementation._validate(root):
                                return_type = type_map[
                                    implementation.graphql_name
                                ].implementation
                                break
                else:
                    return_type = type_map[root_definition.name].implementation

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

    def _validate(self, value):
        # in unions only one type might be valid.
        for type_ in self.types:
            if type_.__validate(value):
                return True
        return False


Types = TypeVar("Types", bound=Type)


# We return a Union type here in order to allow to use the union type as type
# annotation.
# For the `types` argument we'd ideally use a TypeVarTuple, but that's not
# yet supported in any python implementation (or in typing_extensions).
# See https://www.python.org/dev/peps/pep-0646/ for more information
def union(
    name: str,
    types: Tuple[Types, ...],
    *,
    description: str = None,
    directives: Iterable[object] = (),
) -> Union[Types]:
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
        if not isinstance(_type, TypeVar) and not hasattr(_type, "_type_definition"):
            raise InvalidUnionType(
                f"Type `{_type.__name__}` cannot be used in a GraphQL Union"
            )

    union_definition = StrawberryUnion(
        name=name,
        type_annotations=tuple(StrawberryAnnotation(type_) for type_ in types),
        description=description,
        directives=directives,
    )

    return union_definition  # type: ignore
