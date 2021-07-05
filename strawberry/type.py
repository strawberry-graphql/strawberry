from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Mapping, TypeVar, Union


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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StrawberryType):
            if isinstance(other, StrawberryContainer):
                return self.of_type == other.of_type
            else:
                return False

        return super().__eq__(other)

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

        return type(self)(of_type_copy)

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


class StrawberryTypeVar(StrawberryType):
    def __init__(self, type_var: TypeVar):
        self.type_var = type_var

    def copy_with(  # type: ignore[override]
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        return type_var_map[self.type_var]

    @property
    def is_generic(self) -> bool:
        return True

    @property
    def type_params(self) -> List[TypeVar]:
        return [self.type_var]

    def __eq__(self, other) -> bool:
        if isinstance(other, StrawberryTypeVar):
            return self.type_var == other.type_var
        if isinstance(other, TypeVar):
            return self.type_var == other

        return super().__eq__(other)
