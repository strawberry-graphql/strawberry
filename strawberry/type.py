from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, TypeVar, Union


class StrawberryType(ABC):
    @property
    @abstractmethod
    def is_generic(self) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def validate(self, value):
        raise NotImplementedError()

    @staticmethod
    def base_validator(expected_type, value) -> bool:
        from strawberry.types.types import get_type_definition

        # FIXME: This is an  ugly fix for strawberry.type not being a StrawberryObject
        if isinstance(expected_type, StrawberryType):
            return expected_type.validate(value)
        elif definition := get_type_definition(expected_type):
            return definition.validate(value)
        elif isinstance(value, expected_type):
            return True
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
    def __init__(self, of_type: Union[StrawberryType, type]):
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
    def is_generic(self) -> bool:
        from strawberry.types.types import get_type_definition

        type_ = self.of_type
        if strawberry_definition := get_type_definition(self.of_type):
            type_ = strawberry_definition

        if isinstance(type_, StrawberryType):
            return type_.is_generic

        return False

    def validate(self, value):
        if isinstance(self.of_type, StrawberryType):
            if not self.of_type.validate(value):
                return False
        else:
            if not isinstance(value, self.of_type):
                return False
        return True


class StrawberryList(StrawberryContainer):
    def validate(self, value: List[Any]) -> bool:
        for node in value:
            if isinstance(self.of_type, StrawberryType):
                if not self.of_type.validate(node):
                    return False
            else:
                if not isinstance(node, self.of_type):
                    return False
        return True


class StrawberryOptional(StrawberryContainer):
    def validate(self, value: List[Any]) -> bool:
        if value is None:
            return True
        return super().validate(value)


class StrawberryTypeVar(StrawberryType):
    def __init__(self, type_var: TypeVar):
        self.type_var = type_var

    @property
    def is_generic(self) -> bool:
        return True

    def validate(self, value):
        raise NotImplementedError("typeVars cannot be validated")

    def __eq__(self, other) -> bool:
        if isinstance(other, StrawberryTypeVar):
            return self.type_var == other.type_var
        if isinstance(other, TypeVar):
            return self.type_var == other

        return super().__eq__(other)
