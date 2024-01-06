from __future__ import annotations

import dataclasses
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)
from typing_extensions import Self, deprecated

from strawberry.type import (
    StrawberryType,
    StrawberryTypeVar,
    WithStrawberryObjectDefinition,
)
from strawberry.utils.deprecations import DEPRECATION_MESSAGES, DeprecatedDescriptor
from strawberry.utils.inspect import get_specialized_type_var_map
from strawberry.utils.typing import is_generic as is_type_generic

if TYPE_CHECKING:
    from graphql import GraphQLAbstractType, GraphQLResolveInfo

    from strawberry.field import StrawberryField


@dataclasses.dataclass(eq=False)
class StrawberryObjectDefinition(StrawberryType):
    """
    Encapsulates definitions for Input / Object / interface GraphQL Types.

    In order get the definition from a decorated object you can use
    `has_object_definition` or `get_object_definition` as a shortcut.
    """

    name: str
    is_input: bool
    is_interface: bool
    origin: Type[Any]
    description: Optional[str]
    interfaces: List[StrawberryObjectDefinition]
    extend: bool
    directives: Optional[Sequence[object]]
    is_type_of: Optional[Callable[[Any, GraphQLResolveInfo], bool]]
    resolve_type: Optional[
        Callable[[Any, GraphQLResolveInfo, GraphQLAbstractType], str]
    ]

    fields: List[StrawberryField]

    concrete_of: Optional[StrawberryObjectDefinition] = None
    """Concrete implementations of Generic TypeDefinitions fill this in"""
    type_var_map: Mapping[str, Union[StrawberryType, type]] = dataclasses.field(
        default_factory=dict
    )

    def __post_init__(self):
        # resolve `Self` annotation with the origin type
        for index, field in enumerate(self.fields):
            if isinstance(field.type, StrawberryType) and field.type.has_generic(Self):  # type: ignore
                self.fields[index] = field.copy_with({Self.__name__: self.origin})  # type: ignore

    def resolve_generic(self, wrapped_cls: type) -> type:
        from strawberry.annotation import StrawberryAnnotation

        passed_types = wrapped_cls.__args__  # type: ignore
        params = wrapped_cls.__origin__.__parameters__  # type: ignore

        # Make sure all passed_types are turned into StrawberryTypes
        resolved_types = []
        for passed_type in passed_types:
            resolved_type = StrawberryAnnotation(passed_type).resolve()
            resolved_types.append(resolved_type)

        type_var_map = dict(zip((param.__name__ for param in params), resolved_types))

        return self.copy_with(type_var_map)

    def copy_with(
        self, type_var_map: Mapping[str, Union[StrawberryType, type]]
    ) -> Type[WithStrawberryObjectDefinition]:
        fields = [field.copy_with(type_var_map) for field in self.fields]

        new_type_definition = StrawberryObjectDefinition(
            name=self.name,
            is_input=self.is_input,
            origin=self.origin,
            is_interface=self.is_interface,
            directives=self.directives and self.directives[:],
            interfaces=self.interfaces and self.interfaces[:],
            description=self.description,
            extend=self.extend,
            is_type_of=self.is_type_of,
            resolve_type=self.resolve_type,
            fields=fields,
            concrete_of=self,
            type_var_map=type_var_map,
        )

        new_type = type(
            new_type_definition.name,
            (self.origin,),
            {"__strawberry_definition__": new_type_definition},
        )
        # TODO: remove when deprecating _type_definition
        DeprecatedDescriptor(
            DEPRECATION_MESSAGES._TYPE_DEFINITION,
            new_type.__strawberry_definition__,  # type: ignore
            "_type_definition",
        ).inject(new_type)

        new_type_definition.origin = new_type

        return new_type

    def get_field(self, python_name: str) -> Optional[StrawberryField]:
        return next(
            (field for field in self.fields if field.python_name == python_name), None
        )

    @property
    def is_graphql_generic(self) -> bool:
        if not is_type_generic(self.origin):
            return False

        # here we are checking if any exposed field is generic
        # a Strawberry class can be "generic", but not expose any
        # generic field to GraphQL
        return any(field.is_graphql_generic for field in self.fields)

    @property
    def is_specialized_generic(self) -> bool:
        return self.is_graphql_generic and not getattr(
            self.origin, "__parameters__", None
        )

    @property
    def specialized_type_var_map(self) -> Optional[Dict[str, type]]:
        return get_specialized_type_var_map(self.origin)

    @property
    def type_params(self) -> List[TypeVar]:
        type_params: List[TypeVar] = []
        for field in self.fields:
            type_params.extend(field.type_params)

        return type_params

    def is_implemented_by(self, root: Type[WithStrawberryObjectDefinition]) -> bool:
        # TODO: Support dicts
        if isinstance(root, dict):
            raise NotImplementedError

        type_definition = root.__strawberry_definition__

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
            expected_concrete_type = self.type_var_map.get(
                generic_field_type.type_var.__name__
            )
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


# TODO: remove when deprecating _type_definition
if TYPE_CHECKING:

    @deprecated("Use StrawberryObjectDefinition instead")
    class TypeDefinition(StrawberryObjectDefinition):
        ...

else:
    TypeDefinition = StrawberryObjectDefinition
