from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

from strawberry.type import StrawberryType, StrawberryTypeVar
from strawberry.utils.typing import is_generic as is_type_generic


if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo

    from strawberry.field import StrawberryField


@dataclasses.dataclass(eq=False)
class TypeDefinition(StrawberryType):
    name: str
    is_input: bool
    is_interface: bool
    origin: Type
    description: Optional[str]
    interfaces: List["TypeDefinition"]
    extend: bool
    directives: Optional[Sequence[object]]
    is_type_of: Optional[Callable[[Any, GraphQLResolveInfo], bool]]

    _fields: List["StrawberryField"]

    concrete_of: Optional["TypeDefinition"] = None
    """Concrete implementations of Generic TypeDefinitions fill this in"""
    type_var_map: Mapping[TypeVar, Union[StrawberryType, type]] = dataclasses.field(
        default_factory=dict
    )

    # TODO: remove wrapped cls when we "merge" this with `StrawberryObject`
    def resolve_generic(self, wrapped_cls: type) -> type:
        from strawberry.annotation import StrawberryAnnotation

        passed_types = wrapped_cls.__args__  # type: ignore
        params = wrapped_cls.__origin__.__parameters__  # type: ignore

        # Make sure all passed_types are turned into StrawberryTypes
        resolved_types = []
        for passed_type in passed_types:
            resolved_type = StrawberryAnnotation(passed_type).resolve()
            resolved_types.append(resolved_type)

        type_var_map = dict(zip(params, resolved_types))

        return self.copy_with(type_var_map)

    # TODO: Return a StrawberryObject
    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> type:
        fields = []
        for field in self.fields:
            # TODO: Logic unnecessary with StrawberryObject
            field_type = field.type
            if hasattr(field_type, "_type_definition"):
                field_type = field_type._type_definition  # type: ignore

            # TODO: All types should end up being StrawberryTypes
            #       The first check is here as a symptom of strawberry.ID being a
            #       Scalar, but not a StrawberryType
            if isinstance(field_type, StrawberryType) and field_type.is_generic:
                field = field.copy_with(type_var_map)

            fields.append(field)

        new_type_definition = TypeDefinition(
            name=self.name,
            is_input=self.is_input,
            origin=self.origin,
            is_interface=self.is_interface,
            directives=self.directives,
            interfaces=self.interfaces,
            description=self.description,
            extend=self.extend,
            is_type_of=self.is_type_of,
            _fields=fields,
            concrete_of=self,
            type_var_map=type_var_map,
        )

        new_type = type(
            new_type_definition.name,
            (self.origin,),
            {"_type_definition": new_type_definition},
        )

        new_type_definition.origin = new_type

        return new_type

    def get_field(self, python_name: str) -> Optional["StrawberryField"]:
        return next(
            (field for field in self.fields if field.python_name == python_name), None
        )

    @property
    def fields(self) -> List["StrawberryField"]:
        # TODO: rename _fields to fields and remove this property
        return self._fields

    @property
    def is_generic(self) -> bool:
        return is_type_generic(self.origin)

    @property
    def type_params(self) -> List[TypeVar]:
        type_params: List[TypeVar] = []
        for field in self.fields:
            type_params.extend(field.type_params)

        return type_params

    def is_implemented_by(self, root: Union[type, dict]) -> bool:
        # TODO: Accept StrawberryObject instead
        # TODO: Support dicts
        if isinstance(root, dict):
            raise NotImplementedError()

        type_definition = root._type_definition  # type: ignore

        if type_definition is self:
            # No generics involved. Exact type match
            return True

        if type_definition is not self.concrete_of:
            # Either completely different type, or concrete type of a different generic
            return False

        # Check the mapping of all fields' TypeVars
        for generic_field in type_definition.fields:
            generic_field_type = generic_field.type
            if not isinstance(generic_field_type, StrawberryTypeVar):
                continue

            # For each TypeVar found, get the expected type from the copy's type map
            expected_concrete_type = self.type_var_map.get(generic_field_type.type_var)
            if expected_concrete_type is None:
                # TODO: Should this return False?
                continue

            # Check if the expected type matches the type found on the type_map
            real_concrete_type = type(getattr(root, generic_field.name))

            # TODO: uniform type var map, at the moment we map object types
            # to their class (not to TypeDefinition) while we map enum to
            # the EnumDefinition class. This is why we do this check here:
            if hasattr(real_concrete_type, "_enum_definition"):
                real_concrete_type = real_concrete_type._enum_definition

            if real_concrete_type is not expected_concrete_type:
                return False

        # All field mappings succeeded. This is a match
        return True
