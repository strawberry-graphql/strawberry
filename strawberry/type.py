from __future__ import annotations

from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Mapping,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
)

from typing_extensions import Annotated, get_args, get_origin


if TYPE_CHECKING:
    from .types.types import TypeDefinition


class StrawberryType(ABC):
    @property
    def type_params(self) -> List[TypeVar]:
        return []

    @abstractmethod
    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def is_generic(self) -> bool:
        raise NotImplementedError()

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
    def __init__(self, of_type: Union[StrawberryType, type]):
        self.of_type = of_type
        self.args: Tuple[Any, ...] = ()  # Other arguments, used in StrawberryAnnotated

    def __hash__(self) -> int:
        return hash((type(self), self.of_type, self.args))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StrawberryType):
            if type(self) == type(other):
                other = cast(StrawberryContainer, other)
                return (self.of_type, self.args) == (other.of_type, other.args)
            else:
                return False

        return super().__eq__(other)

    def __repr__(self) -> str:
        of_type_name = (
            self.of_type.__name__
            if isinstance(self.of_type, type)
            else repr(self.of_type)
        )
        args = ", ".join((of_type_name,) + tuple(map(repr, self.args)))
        return f"{type(self).__name__}[{args}]"

    @property
    def type_params(self) -> List[TypeVar]:
        if hasattr(self.of_type, "_type_definition"):
            parameters = getattr(self.of_type, "__parameters__", None)

            return list(parameters) if parameters else []

        elif isinstance(self.of_type, StrawberryType):
            return self.of_type.type_params

        else:
            return []

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> StrawberryType:
        of_type_copy: Union[StrawberryType, type]

        # TODO: Obsolete with StrawberryObject
        if hasattr(self.of_type, "_type_definition"):
            type_definition: TypeDefinition = (
                self.of_type._type_definition  # type: ignore
            )

            if type_definition.is_generic:
                of_type_copy = type_definition.copy_with(type_var_map)

        elif isinstance(self.of_type, StrawberryType) and self.of_type.is_generic:
            of_type_copy = self.of_type.copy_with(type_var_map)

        assert of_type_copy

        return type(self)(of_type_copy, *self.args)

    @property
    def is_generic(self) -> bool:
        # TODO: Obsolete with StrawberryObject
        type_ = self.of_type
        if hasattr(self.of_type, "_type_definition"):
            type_ = self.of_type._type_definition  # type: ignore

        if isinstance(type_, StrawberryType):
            return type_.is_generic

        return False


class StrawberryList(StrawberryContainer):
    ...


class StrawberryOptional(StrawberryContainer):
    ...


class StrawberryAnnotated(StrawberryContainer):
    """Equivalent to typing.Annotated for Strawberry types"""

    def __init__(self, of_type: Union[StrawberryType, type], *args):
        of_type, base_args = StrawberryAnnotated.get_type_and_args(of_type)
        super().__init__(of_type)
        self.args = tuple(base_args) + args

    T = TypeVar("T")

    @staticmethod
    def get_type_and_args(
        type_: Union[StrawberryType, type, T]
    ) -> Tuple[Union[StrawberryType, type, T], Sequence[Any]]:
        """
        Splits a possibly-annotated type in the actual type and the list of annotations
        Supports both StrawberryAnnotated and typing.Annotated
        """
        args: Tuple[Any, ...] = ()
        while True:
            if isinstance(type_, StrawberryAnnotated):
                args = type_.args + args
                type_ = type_.of_type
            elif get_origin(type_) is Annotated:
                base_args = get_args(type_)
                type_ = base_args[0]
                args = base_args[1:] + args
            else:
                return type_, args


class StrawberryTypeVar(StrawberryType):
    def __init__(self, type_var: TypeVar):
        self.type_var = type_var

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        return type_var_map[self.type_var]

    @property
    def is_generic(self) -> bool:
        return True

    @property
    def type_params(self) -> List[TypeVar]:
        return [self.type_var]

    def __hash__(self) -> int:
        return hash(self.type_var)

    def __eq__(self, other) -> bool:
        if isinstance(other, StrawberryTypeVar):
            return self.type_var == other.type_var
        if isinstance(other, TypeVar):
            return self.type_var == other

        return super().__eq__(other)

    def __repr__(self) -> str:
        return f"{type(self).__name__}[{self.type_var.__name__}]"
