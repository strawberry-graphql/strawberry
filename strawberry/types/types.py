import dataclasses
from strawberry.utils.str_converters import capitalize_first
from typing import TYPE_CHECKING, Dict, List, Mapping, Optional, Type, TypeVar, Union

from strawberry.type import StrawberryType, StrawberryTypeVar


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
    is_generic: bool
    origin: Type
    description: Optional[str]
    federation: FederationTypeParams
    interfaces: List["TypeDefinition"]

    _fields: List["StrawberryField"]
    _type_params: Dict[str, Type] = dataclasses.field(default_factory=dict, init=False)

    # TODO: remove wrapped cls when we "merge" this with `StrawberryObjectType`
    def resolve_generic(self, wrapped_cls: type) -> type:
        passed_types = wrapped_cls.__args__
        params = wrapped_cls.__origin__.__parameters__
        typevar_map = dict(zip(params, passed_types))
        type_definition = self.copy_with(typevar_map)

        return type(
            type_definition.name,
            (),
            {"_type_definition": type_definition},
        )

    def copy_with(
        self, typevar_map: Optional[Mapping[TypeVar, Union[StrawberryType, type]]]
    ) -> "TypeDefinition":
        name = self.get_name_from_types(typevar_map.values())

        fields = []

        for field in self.fields:
            if isinstance(field.type, StrawberryTypeVar):
                field.type = typevar_map[field.type.type_var]

            fields.append(field)

        return TypeDefinition(
            name=name,
            is_input=self.is_input,
            origin=self.origin,
            is_interface=self.is_interface,
            is_generic=False,
            federation=self.federation,
            interfaces=self.interfaces,
            description=self.description,
            _fields=fields,
        )

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
    def type_params(self) -> Dict[str, Type]:
        if not self._type_params:
            from .type_resolver import _get_type_params

            self._type_params = _get_type_params(self.fields)

        return self._type_params


@dataclasses.dataclass
class FederationFieldParams:
    provides: List[str] = dataclasses.field(default_factory=list)
    requires: List[str] = dataclasses.field(default_factory=list)
    external: bool = False
