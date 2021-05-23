from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Mapping, TypeVar, Union


class StrawberryType(ABC):
    @property
    def type_params(self) -> List[TypeVar]:
        return []

    @abstractmethod
    def copy_with(
        self, typevar_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> StrawberryType:
        raise NotImplementedError()


class StrawberryContainer(StrawberryType):
    def __init__(self, of_type: StrawberryType):
        self.of_type = of_type

    @property
    def type_params(self) -> List[TypeVar]:
        if hasattr(self.of_type, "_type_definition"):
            parameters = getattr(self.of_type, "__parameters__", None)

            return list(parameters) if parameters else []

        return self.of_type.type_params

    def copy_with(
        self, typevar_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> StrawberryType:
        return super().copy_with(typevar_map)


class StrawberryList(StrawberryContainer):
    ...


class StrawberryOptional(StrawberryContainer):
    ...


class StrawberryTypeVar(StrawberryType):
    def __init__(self, type_var: TypeVar):
        self.type_var = type_var

    def copy_with(
        self, typevar_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> StrawberryType:
        return super().copy_with(typevar_map)

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
