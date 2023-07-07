from __future__ import annotations

import itertools
import sys
import warnings
from itertools import chain
from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    Iterable,
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
from typing_extensions import Annotated, get_origin

from graphql import GraphQLNamedType, GraphQLUnionType

from strawberry.annotation import StrawberryAnnotation
from strawberry.exceptions import (
    InvalidTypeForUnionMergeError,
    InvalidUnionTypeError,
    UnallowedReturnTypeForUnion,
    WrongReturnTypeForUnion,
)
from strawberry.exceptions.handler import should_use_rich_exceptions
from strawberry.lazy_type import LazyType
from strawberry.type import (
    StrawberryOptional,
    StrawberryType,
    has_object_definition,
)

if TYPE_CHECKING:
    from graphql import (
        GraphQLAbstractType,
        GraphQLResolveInfo,
        GraphQLType,
        GraphQLTypeResolver,
    )

    from strawberry.schema.types.concrete_type import TypeMap


class StrawberryUnion(StrawberryType):
    # used for better error messages
    _source_file: Optional[str] = None
    _source_line: Optional[int] = None

    def __init__(
        self,
        name: Optional[str] = None,
        type_annotations: Tuple[StrawberryAnnotation, ...] = tuple(),
        description: Optional[str] = None,
        directives: Iterable[object] = (),
    ):
        self.graphql_name = name
        self.type_annotations = type_annotations
        self.description = description
        self.directives = directives
        self._source_file = None
        self._source_line = None

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
        return hash((self.graphql_name, self.type_annotations, self.description))

    def __or__(self, other: Union[StrawberryType, type]) -> StrawberryType:
        # TODO: this will be removed in future versions, you should
        # use Annotated[Union[...], strawberry.union(...)] instead

        if other is None:
            # Return the correct notation when using `StrawberryUnion | None`.
            return StrawberryOptional(of_type=self)

        raise InvalidTypeForUnionMergeError(self, other)

    @property
    def types(self) -> Tuple[StrawberryType, ...]:
        return tuple(
            cast(StrawberryType, annotation.resolve())
            for annotation in self.type_annotations
        )

    @property
    def type_params(self) -> List[TypeVar]:
        def _get_type_params(type_: StrawberryType):
            if isinstance(type_, LazyType):
                type_ = cast("StrawberryType", type_.resolve_type())

            if has_object_definition(type_):
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
        def _is_generic(type_: object) -> bool:
            if has_object_definition(type_):
                type_ = type_.__strawberry_definition__

            if isinstance(type_, StrawberryType):
                return type_.is_generic

            return False

        return any(map(_is_generic, self.types))

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> StrawberryType:
        if not self.is_generic:
            return self

        new_types = []
        for type_ in self.types:
            new_type: Union[StrawberryType, type]

            if has_object_definition(type_):
                type_definition = type_.__strawberry_definition__

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

    def __call__(self, *args: str, **kwargs: Any) -> NoReturn:
        """Do not use.

        Used to bypass
        https://github.com/python/cpython/blob/5efb1a77e75648012f8b52960c8637fc296a5c6d/Lib/typing.py#L148-L149
        """
        raise ValueError("Cannot use union type directly")

    def get_type_resolver(self, type_map: TypeMap) -> GraphQLTypeResolver:
        def _resolve_union_type(
            root: Any, info: GraphQLResolveInfo, type_: GraphQLAbstractType
        ) -> str:
            assert isinstance(type_, GraphQLUnionType)

            from strawberry.types.types import StrawberryObjectDefinition

            # If the type given is not an Object type, try resolving using `is_type_of`
            # defined on the union's inner types
            if not has_object_definition(root):
                for inner_type in type_.types:
                    if inner_type.is_type_of is not None and inner_type.is_type_of(
                        root, info
                    ):
                        return inner_type.name

                # Couldn't resolve using `is_type_of`
                raise WrongReturnTypeForUnion(info.field_name, str(type(root)))

            return_type: Optional[GraphQLType]

            # Iterate over all of our known types and find the first concrete
            # type that implements the type. We prioritise checking types named in the
            # Union in case a nested generic object matches against more than one type.
            concrete_types_for_union = (type_map[x.name] for x in type_.types)

            # TODO: do we still need to iterate over all types in `type_map`?
            for possible_concrete_type in chain(
                concrete_types_for_union, type_map.values()
            ):
                possible_type = possible_concrete_type.definition
                if not isinstance(possible_type, StrawberryObjectDefinition):
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
                # TODO: check if this is correct
                return return_type.__name__  # type: ignore

        return _resolve_union_type

    @staticmethod
    def is_valid_union_type(type_: object) -> bool:
        # Usual case: Union made of @strawberry.types
        if has_object_definition(type_):
            return True

        # Can't confidently assert that these types are valid/invalid within Unions
        # until full type resolving stage is complete

        ignored_types = (LazyType, TypeVar)

        if isinstance(type_, ignored_types):
            return True

        if isinstance(type_, StrawberryUnion):
            return True

        if get_origin(type_) is Annotated:
            return True

        return False


def union(
    name: str,
    types: Optional[Collection[Type[Any]]] = None,
    *,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> StrawberryUnion:
    """Creates a new named Union type.

    Example usages:

    >>> @strawberry.type
    ... class A: ...
    >>> @strawberry.type
    ... class B: ...
    >>> Annotated[A | B, strawberry.union("Name")]
    """

    if types is None:
        union = StrawberryUnion(
            name=name,
            description=description,
            directives=directives,
        )

        if should_use_rich_exceptions():
            frame = sys._getframe(1)

            union._source_file = frame.f_code.co_filename
            union._source_line = frame.f_lineno

        return union

    warnings.warn(
        (
            "Passing types to `strawberry.union` is deprecated. Please use "
            f'{name} = Annotated[Union[A, B], strawberry.union("{name}")] instead'
        ),
        DeprecationWarning,
        stacklevel=2,
    )

    # Validate types
    if not types:
        raise TypeError("No types passed to `union`")

    for type_ in types:
        # Due to TypeVars, Annotations, LazyTypes, etc., this does not perfectly detect
        # issues. This check also occurs in the Schema conversion stage as a backup.
        if not StrawberryUnion.is_valid_union_type(type_):
            raise InvalidUnionTypeError(union_name=name, invalid_type=type_)

    return StrawberryUnion(
        name=name,
        type_annotations=tuple(StrawberryAnnotation(type_) for type_ in types),
        description=description,
        directives=directives,
    )
