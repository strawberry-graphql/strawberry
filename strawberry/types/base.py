from __future__ import annotations

import dataclasses
from abc import ABC, abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    overload,
)
from typing_extensions import Literal, Protocol, Self, deprecated

from strawberry.utils.deprecations import DEPRECATION_MESSAGES, DeprecatedDescriptor
from strawberry.utils.inspect import get_specialized_type_var_map
from strawberry.utils.typing import is_concrete_generic
from strawberry.utils.typing import is_generic as is_type_generic

if TYPE_CHECKING:
    from typing_extensions import TypeGuard

    from graphql import GraphQLAbstractType, GraphQLResolveInfo

    from strawberry.types.field import StrawberryField


class StrawberryType(ABC):
    """The base class for all types that Strawberry uses.

    Every type that is decorated by strawberry should have a dunder
    `__strawberry_definition__` with an instance of a StrawberryType that contains
    the parsed information that strawberry created.

    NOTE: ATM this is only true for @type @interface @input follow
    https://github.com/strawberry-graphql/strawberry/issues/2841 to see progress.
    """

    @property
    def type_params(self) -> List[TypeVar]:
        return []

    @property
    def is_one_of(self) -> bool:
        return False

    @abstractmethod
    def copy_with(
        self,
        type_var_map: Mapping[
            str, Union[StrawberryType, Type[WithStrawberryObjectDefinition]]
        ],
    ) -> Union[StrawberryType, Type[WithStrawberryObjectDefinition]]:
        raise NotImplementedError()

    @property
    @abstractmethod
    def is_graphql_generic(self) -> bool:
        raise NotImplementedError()

    def has_generic(self, type_var: TypeVar) -> bool:
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
    def __init__(
        self, of_type: Union[StrawberryType, Type[WithStrawberryObjectDefinition], type]
    ) -> None:
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
    def type_params(self) -> List[TypeVar]:
        if has_object_definition(self.of_type):
            parameters = getattr(self.of_type, "__parameters__", None)

            return list(parameters) if parameters else []

        elif isinstance(self.of_type, StrawberryType):
            return self.of_type.type_params

        else:
            return []

    def copy_with(
        self,
        type_var_map: Mapping[
            str, Union[StrawberryType, Type[WithStrawberryObjectDefinition]]
        ],
    ) -> Self:
        of_type_copy = self.of_type

        if has_object_definition(self.of_type):
            type_definition = self.of_type.__strawberry_definition__

            if type_definition.is_graphql_generic:
                of_type_copy = type_definition.copy_with(type_var_map)

        elif (
            isinstance(self.of_type, StrawberryType) and self.of_type.is_graphql_generic
        ):
            of_type_copy = self.of_type.copy_with(type_var_map)

        return type(self)(of_type_copy)

    @property
    def is_graphql_generic(self) -> bool:
        from strawberry.schema.compat import is_graphql_generic

        type_ = self.of_type

        return is_graphql_generic(type_)

    def has_generic(self, type_var: TypeVar) -> bool:
        if isinstance(self.of_type, StrawberryType):
            return self.of_type.has_generic(type_var)
        return False


class StrawberryList(StrawberryContainer): ...


class StrawberryOptional(StrawberryContainer): ...


class StrawberryTypeVar(StrawberryType):
    def __init__(self, type_var: TypeVar) -> None:
        self.type_var = type_var

    def copy_with(
        self, type_var_map: Mapping[str, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        return type_var_map[self.type_var.__name__]

    @property
    def is_graphql_generic(self) -> bool:
        return True

    def has_generic(self, type_var: TypeVar) -> bool:
        return self.type_var == type_var

    @property
    def type_params(self) -> List[TypeVar]:
        return [self.type_var]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StrawberryTypeVar):
            return self.type_var == other.type_var
        if isinstance(other, TypeVar):
            return self.type_var == other

        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.type_var)


class WithStrawberryObjectDefinition(Protocol):
    __strawberry_definition__: ClassVar[StrawberryObjectDefinition]


def has_object_definition(
    obj: Any,
) -> TypeGuard[Type[WithStrawberryObjectDefinition]]:
    if hasattr(obj, "__strawberry_definition__"):
        return True
    # TODO: Generics remove dunder members here, so we inject it here.
    #  Would be better to avoid it somehow.
    # https://github.com/python/cpython/blob/3a314f7c3df0dd7c37da7d12b827f169ee60e1ea/Lib/typing.py#L1152
    if is_concrete_generic(obj):
        concrete = obj.__origin__
        if hasattr(concrete, "__strawberry_definition__"):
            obj.__strawberry_definition__ = concrete.__strawberry_definition__
            return True
    return False


@overload
def get_object_definition(
    obj: Any,
    *,
    strict: Literal[True],
) -> StrawberryObjectDefinition: ...


@overload
def get_object_definition(
    obj: Any,
    *,
    strict: bool = False,
) -> Optional[StrawberryObjectDefinition]: ...


def get_object_definition(
    obj: Any,
    *,
    strict: bool = False,
) -> Optional[StrawberryObjectDefinition]:
    definition = obj.__strawberry_definition__ if has_object_definition(obj) else None
    if strict and definition is None:
        raise TypeError(f"{obj!r} does not have a StrawberryObjectDefinition")

    return definition


@dataclasses.dataclass(eq=False)
class StrawberryObjectDefinition(StrawberryType):
    """Encapsulates definitions for Input / Object / interface GraphQL Types.

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

    def __post_init__(self) -> None:
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
    def is_object_type(self) -> bool:
        return not self.is_input and not self.is_interface

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
        for field in type_definition.fields:
            if not field.is_graphql_generic:
                continue

            value = getattr(root, field.name)
            generic_field_type = field.type

            while isinstance(generic_field_type, StrawberryList):
                generic_field_type = generic_field_type.of_type

                assert isinstance(value, (list, tuple))

                if len(value) == 0:
                    # We can't infer the type of an empty list, so we just
                    # return the first one we find
                    return True

                value = value[0]

            if isinstance(generic_field_type, StrawberryTypeVar):
                type_var = generic_field_type.type_var
            # TODO: I don't think we support nested types properly
            # if there's a union that has two nested types that
            # are have the same field with different types, we might
            # not be able to differentiate them
            else:
                continue

            # For each TypeVar found, get the expected type from the copy's type map
            expected_concrete_type = self.type_var_map.get(type_var.__name__)

            # this shouldn't happen, but we do a defensive check just in case
            if expected_concrete_type is None:
                continue

            # Check if the expected type matches the type found on the type_map
            real_concrete_type = type(value)

            # TODO: uniform type var map, at the moment we map object types
            # to their class (not to TypeDefinition) while we map enum to
            # the EnumDefinition class. This is why we do this check here:
            if hasattr(real_concrete_type, "_enum_definition"):
                real_concrete_type = real_concrete_type._enum_definition

            if isinstance(expected_concrete_type, type) and issubclass(
                real_concrete_type, expected_concrete_type
            ):
                return True

            if real_concrete_type is not expected_concrete_type:
                return False

        # All field mappings succeeded. This is a match
        return True

    @property
    def is_one_of(self) -> bool:
        from strawberry.schema_directives import OneOf

        if not self.is_input or not self.directives:
            return False

        return any(isinstance(directive, OneOf) for directive in self.directives)


# TODO: remove when deprecating _type_definition
if TYPE_CHECKING:

    @deprecated("Use StrawberryObjectDefinition instead")
    class TypeDefinition(StrawberryObjectDefinition): ...

else:
    TypeDefinition = StrawberryObjectDefinition


__all__ = [
    "StrawberryContainer",
    "StrawberryList",
    "StrawberryObjectDefinition",
    "StrawberryOptional",
    "StrawberryType",
    "StrawberryTypeVar",
    "TypeDefinition",
    "WithStrawberryObjectDefinition",
    "get_object_definition",
    "has_object_definition",
]
