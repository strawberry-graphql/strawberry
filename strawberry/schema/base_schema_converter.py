from abc import ABC, abstractmethod
from typing import Any

from typing_extensions import TypeAlias

from strawberry.custom_scalar import ScalarDefinition
from strawberry.enum import EnumDefinition, EnumValue
from strawberry.field import StrawberryField
from strawberry.types.fields.resolver import StrawberryResolver
from strawberry.union import StrawberryUnion


# Temporary until Strawberry types are fully implemented
StrawberryType: TypeAlias = Any
StrawberryEnum: TypeAlias = EnumDefinition
StrawberryEnumValue: TypeAlias = EnumValue
StrawberryInterface: TypeAlias = Any
StrawberryList: TypeAlias = Any
StrawberryObjectType: TypeAlias = Any
StrawberryOptional: TypeAlias = Any
StrawberryScalar: TypeAlias = ScalarDefinition


class AbstractSchemaConverter(ABC):
    @classmethod
    @abstractmethod
    def get_graphql_type(cls, type_: StrawberryType) -> ...:
        # TODO
        ...
        # if isinstance(type_, StrawberryOptional):
        #     return cls.from_optional(type_)
        #
        # # if isinstance(type_, StrawberryObjectType):
        # if hasattr(type_, "_type_definition"):
        #     ...
        # elif isinstance(type_, StrawberryEnum):
        #     graphql_type = cls.from_enum(type_)
        # elif isinstance(type_, StrawberryList):
        #     graphql_type = cls.from_list(type_)
        # elif isinstance(type_, StrawberryScalar):
        #     graphql_type = cls.from_scalar(type_)
        # elif isinstance(type_, StrawberryUnion):
        #     graphql_type = cls.from_union(type_)
        # else:
        #     raise TypeError(f"Unexpected type '{type_}'")
        #
        # # TODO: Allow this to be abstracted
        # graphql_type = GraphQLNullableType(graphql_type)
        #
        # return graphql_type

    @classmethod
    @abstractmethod
    def from_enum(cls, enum: StrawberryEnum) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_enum_value(cls, enum_value: StrawberryEnumValue) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_field(cls, field: StrawberryField) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_input_field(cls, field: ...) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_input_object_type(cls, object_type: Any) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_interface(cls, interface: StrawberryInterface) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_list(cls, list_: StrawberryList) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_object_type(cls, object_type: StrawberryObjectType) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_optional(cls, optional: StrawberryOptional) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_resolver(cls, resolver: StrawberryResolver) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_scalar(cls, scalar: StrawberryScalar) -> ...:
        ...

    @classmethod
    @abstractmethod
    def from_union(cls, union: StrawberryUnion) -> ...:
        ...
