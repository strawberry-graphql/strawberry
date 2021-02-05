import dataclasses
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Type, Union

from strawberry.permission import BasePermission
from strawberry.union import StrawberryUnion


if TYPE_CHECKING:
    from strawberry.types.fields.resolver import StrawberryResolver

undefined = object()


@dataclasses.dataclass
class FederationTypeParams:
    keys: List[str] = dataclasses.field(default_factory=list)
    extend: bool = False


@dataclasses.dataclass
class TypeDefinition:
    name: str
    is_input: bool
    is_interface: bool
    is_generic: bool
    origin: Type
    description: Optional[str]
    federation: FederationTypeParams
    interfaces: List["TypeDefinition"]

    _fields: List["FieldDefinition"]
    _type_params: Dict[str, Type] = dataclasses.field(default_factory=dict, init=False)

    def get_field(self, name: str) -> Optional["FieldDefinition"]:
        return next((field for field in self.fields if field.name == name), None)

    @property
    def fields(self) -> List["FieldDefinition"]:
        from .type_resolver import _resolve_types

        return _resolve_types(self._fields)

    @property
    def type_params(self) -> Dict[str, Type]:
        if not self._type_params:
            from .type_resolver import _get_type_params

            self._type_params = _get_type_params(self.fields)

        return self._type_params


@dataclasses.dataclass
class ArgumentDefinition:
    name: Optional[str] = None
    origin_name: Optional[str] = None
    type: Optional[Type] = None
    origin: Optional[Type] = None
    child: Optional["ArgumentDefinition"] = None
    is_subscription: bool = False
    is_optional: bool = False
    is_child_optional: bool = False
    is_list: bool = False
    is_union: bool = False
    description: Optional[str] = None
    default_value: Any = undefined


@dataclasses.dataclass
class FederationFieldParams:
    provides: List[str] = dataclasses.field(default_factory=list)
    requires: List[str] = dataclasses.field(default_factory=list)
    external: bool = False


@dataclasses.dataclass
class FieldDefinition:
    name: Optional[str]
    origin_name: Optional[str]
    type: Optional[Union[Type, StrawberryUnion]]
    origin: Optional[Union[Type, Callable]] = None
    child: Optional["FieldDefinition"] = None
    is_subscription: bool = False
    is_optional: bool = False
    is_child_optional: bool = False
    is_list: bool = False
    is_union: bool = False
    federation: FederationFieldParams = dataclasses.field(
        default_factory=FederationFieldParams
    )
    arguments: List[ArgumentDefinition] = dataclasses.field(default_factory=list)
    description: Optional[str] = None
    base_resolver: Optional["StrawberryResolver"] = None
    permission_classes: List[Type[BasePermission]] = dataclasses.field(
        default_factory=list
    )
    default_value: Any = undefined
    deprecation_reason: Optional[str] = None
