from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Mapping, TypeVar, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from strawberry.annotation import StrawberryAnnotation


class StrawberryType(ABC):
    @property
    def type_params(self) -> List[TypeVar]:
        return []

    @abstractmethod
    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> StrawberryType:
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
                return False

    def __hash__(self) -> int:
        # TODO: Is this a bad idea? __eq__ objects are supposed to have the same hash
        return id(self)


class StrawberryContainer(StrawberryType):
    def __init__(self, of_type: StrawberryType):
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

        return self.of_type.type_params

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> StrawberryType:
        # TODO: Obsolete with StrawberryObject
        if (
            hasattr(self.of_type, "_type_definition")
            and self.of_type._type_definition.is_generic
        ):
            type_ = self.of_type._type_definition
            of_type_copy = type_.copy_with(type_var_map)

            of_type_copy = type(
                of_type_copy.name,
                (),
                {"_type_definition": of_type_copy},
            )

        elif isinstance(self.of_type, StrawberryType) and self.of_type.is_generic:
            of_type_copy = self.of_type.copy_with(type_var_map)

        else:
            return type(self)(self.of_type)

        return type(self)(of_type_copy)

    @property
    def is_generic(self) -> bool:
        # TODO: Obsolete with StrawberryObject
        type_ = self.of_type
        if hasattr(self.of_type, "_type_definition"):
            type_ = self.of_type._type_definition

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

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> StrawberryType:
        return type_var_map[self.type_var]

    @property
    def is_generic(self) -> bool:
        return True

    @property
    def type_params(self) -> List[TypeVar]:
        return [self.type_var]



# @property
# def type_params(self) -> Optional[List[Type]]:
#     if isinstance(self.type, StrawberryList):
#         assert self.child is not None
#         return self.child.type_params
#
#     if isinstance(self.type, StrawberryUnion):
#         types = self.type.types
#         type_vars = [t for t in types if is_type_var(t)]
#
#         if type_vars:
#             return type_vars
#
#     if is_type_var(self.type):
#         return [self.type]
#
#     if has_type_var(self.type):
#         return get_parameters(self.type)
#
#     return None
