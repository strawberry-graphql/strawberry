from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)
from typing_extensions import Literal, Protocol, Self

from strawberry.utils.typing import is_concrete_generic

if TYPE_CHECKING:
    from typing_extensions import TypeGuard

    from strawberry.types.types import StrawberryObjectDefinition


class StrawberryType(ABC):
    """
    Every type that is decorated by strawberry should have a dunder
    `__strawberry_definition__` with instance of a StrawberryType that contains
    the parsed information that strawberry created.

    NOTE: ATM this is only true for @type @interface @input follow https://github.com/strawberry-graphql/strawberry/issues/2841
    to see progress.
    """

    @property
    def type_params(self) -> List[TypeVar]:
        return []

    @property
    def is_one_of(self) -> bool:
        return False

    @abstractmethod
    def copy_with(
        self,
        type_var_map: Mapping[
            str, Union[StrawberryType, Type[WithStrawberryObjectDefinition]]
        ],
    ) -> Union[StrawberryType, Type[WithStrawberryObjectDefinition]]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def is_graphql_generic(self) -> bool:
        raise NotImplementedError()

    def has_generic(self, type_var: TypeVar) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        from strawberry.annotation import StrawberryAnnotation

        if isinstance(other, StrawberryType):
            return self is other

        elif isinstance(other, StrawberryAnnotation):
            return self == other.resolve()

        else:
            # This could be simplified if StrawberryAnnotation.resolve() always returned
            # a StrawberryType
            resolved = StrawberryAnnotation(other).resolve()
            if isinstance(resolved, StrawberryType):
                return self == resolved
            else:
                return NotImplemented

    def __hash__(self) -> int:
        # TODO: Is this a bad idea? __eq__ objects are supposed to have the same hash
        return id(self)


class StrawberryContainer(StrawberryType):
    def __init__(
        self, of_type: Union[StrawberryType, Type[WithStrawberryObjectDefinition], type]
    ) -> None:
        self.of_type = of_type

    def __hash__(self) -> int:
        return hash((self.__class__, self.of_type))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StrawberryType):
            if isinstance(other, StrawberryContainer):
                return self.of_type == other.of_type
            else:
                return False

        return super().__eq__(other)

    @property
    def type_params(self) -> List[TypeVar]:
        if has_object_definition(self.of_type):
            parameters = getattr(self.of_type, "__parameters__", None)

            return list(parameters) if parameters else []

        elif isinstance(self.of_type, StrawberryType):
            return self.of_type.type_params

        else:
            return []

    def copy_with(
        self,
        type_var_map: Mapping[
            str, Union[StrawberryType, Type[WithStrawberryObjectDefinition]]
        ],
    ) -> Self:
        of_type_copy = self.of_type

        if has_object_definition(self.of_type):
            type_definition = self.of_type.__strawberry_definition__

            if type_definition.is_graphql_generic:
                of_type_copy = type_definition.copy_with(type_var_map)

        elif (
            isinstance(self.of_type, StrawberryType) and self.of_type.is_graphql_generic
        ):
            of_type_copy = self.of_type.copy_with(type_var_map)

        return type(self)(of_type_copy)

    @property
    def is_graphql_generic(self) -> bool:
        from strawberry.schema.compat import is_graphql_generic

        type_ = self.of_type

        return is_graphql_generic(type_)

    def has_generic(self, type_var: TypeVar) -> bool:
        if isinstance(self.of_type, StrawberryType):
            return self.of_type.has_generic(type_var)
        return False


class StrawberryList(StrawberryContainer): ...


class StrawberryOptional(StrawberryContainer): ...


class StrawberryTypeVar(StrawberryType):
    def __init__(self, type_var: TypeVar) -> None:
        self.type_var = type_var

    def copy_with(
        self, type_var_map: Mapping[str, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        return type_var_map[self.type_var.__name__]

    @property
    def is_graphql_generic(self) -> bool:
        return True

    def has_generic(self, type_var: TypeVar) -> bool:
        return self.type_var == type_var

    @property
    def type_params(self) -> List[TypeVar]:
        return [self.type_var]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StrawberryTypeVar):
            return self.type_var == other.type_var
        if isinstance(other, TypeVar):
            return self.type_var == other

        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.type_var)


class WithStrawberryObjectDefinition(Protocol):
    __strawberry_definition__: ClassVar[StrawberryObjectDefinition]


def has_object_definition(
    obj: Any,
) -> TypeGuard[Type[WithStrawberryObjectDefinition]]:
    if hasattr(obj, "__strawberry_definition__"):
        return True
    # TODO: Generics remove dunder members here, so we inject it here.
    #  Would be better to avoid it somehow.
    # https://github.com/python/cpython/blob/3a314f7c3df0dd7c37da7d12b827f169ee60e1ea/Lib/typing.py#L1152
    if is_concrete_generic(obj):
        concrete = obj.__origin__
        if hasattr(concrete, "__strawberry_definition__"):
            obj.__strawberry_definition__ = concrete.__strawberry_definition__
            return True
    return False


@overload
def get_object_definition(
    obj: Any,
    *,
    strict: Literal[True],
) -> StrawberryObjectDefinition: ...


@overload
def get_object_definition(
    obj: Any,
    *,
    strict: bool = False,
) -> Optional[StrawberryObjectDefinition]: ...


def get_object_definition(
    obj: Any,
    *,
    strict: bool = False,
) -> Optional[StrawberryObjectDefinition]:
    definition = obj.__strawberry_definition__ if has_object_definition(obj) else None
    if strict and definition is None:
        raise TypeError(f"{obj!r} does not have a StrawberryObjectDefinition")
    return definition
