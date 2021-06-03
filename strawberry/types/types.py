import dataclasses
from typing import TYPE_CHECKING, Dict, List, Mapping, Optional, Type, TypeVar, Union

from strawberry.type import StrawberryType
from strawberry.utils.str_converters import capitalize_first


if TYPE_CHECKING:
    from strawberry.field import StrawberryField

undefined = object()


@dataclasses.dataclass
class FederationTypeParams:
    keys: List[str] = dataclasses.field(default_factory=list)
    extend: bool = False


@dataclasses.dataclass
class TypeDefinition(StrawberryType):
    name: str
    is_input: bool
    is_interface: bool
    origin: Type
    description: Optional[str]
    federation: FederationTypeParams
    interfaces: List["TypeDefinition"]

    _fields: List["StrawberryField"]
    _type_params: Dict[str, Type] = dataclasses.field(default_factory=dict, init=False)

    # TODO: remove wrapped cls when we "merge" this with `StrawberryObject`
    def resolve_generic(self, wrapped_cls: type) -> type:
        passed_types = wrapped_cls.__args__
        params = wrapped_cls.__origin__.__parameters__

        type_var_map = dict(zip(params, passed_types))
        new_type = self.copy_with(type_var_map)

        return new_type

    # TODO: Return a StrawberryObject
    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> Type:
        name = self.get_name_from_types(type_var_map.values())

        fields = []
        for field in self.fields:
            # TODO: Logic unnecessary with StrawberryObject
            field_type = field.type
            if hasattr(field_type, "_type_definition"):
                field_type = field_type._type_definition

            # TODO: All types should end up being StrawberryTypes
            #       The first check is here as a symptom of strawberry.ID being a
            #       Scalar, but not a StrawberryType
            if isinstance(field_type, StrawberryType) and field_type.is_generic:
                field = field.copy_with(type_var_map)

            fields.append(field)

        type_definition = TypeDefinition(
            name=name,
            is_input=self.is_input,
            origin=self.origin,
            is_interface=self.is_interface,
            federation=self.federation,
            interfaces=self.interfaces,
            description=self.description,
            _fields=fields,
        )

        new_type = type(
            type_definition.name,
            (),
            {"_type_definition": type_definition},
        )

        return new_type

    def get_field(self, name: str) -> Optional["StrawberryField"]:
        return next(
            (field for field in self.fields if field.graphql_name == name), None
        )

    def get_name_from_types(self, types: Union[StrawberryType, type]) -> str:
        from strawberry.union import StrawberryUnion

        names = []

        for type_ in types:
            if isinstance(type_, StrawberryUnion):
                return type_.name
            elif hasattr(type_, "_type_definition"):
                name = capitalize_first(type_._type_definition.name)
            else:
                name = capitalize_first(type_.__name__)

            names.append(name)

        return "".join(names) + self.name

    @property
    def fields(self) -> List["StrawberryField"]:
        # TODO: Remove
        return self._fields

    @property
    def is_generic(self) -> bool:
        for field in self.fields:
            # TODO: Obsolete with StrawberryObject
            if hasattr(field.type, "_type_definition"):
                type_ = field.type._type_definition
            else:
                type_ = field.type

            if isinstance(type_, StrawberryType):
                if type_.is_generic:
                    return True
        return False

        # TODO: Consider making leaf types always StrawberryTypes, maybe a
        #       StrawberryBaseType or something
        # return any(field.type.is_generic for field in self.fields)

    @property
    def type_params(self) -> List[TypeVar]:
        type_params: List[TypeVar] = []
        for field in self.fields:
            type_params.extend(field.type_params)

        return type_params


@dataclasses.dataclass
class FederationFieldParams:
    provides: List[str] = dataclasses.field(default_factory=list)
    requires: List[str] = dataclasses.field(default_factory=list)
    external: bool = False
