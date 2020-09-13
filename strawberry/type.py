import dataclasses
import typing
from functools import partial
from typing import Dict, List, Optional, Type, cast

from graphql import GraphQLObjectType

from strawberry.utils.typing import is_generic
from .exceptions import MissingFieldAnnotationError
from .field import StrawberryField
from .types.type_resolver import _get_fields
from .types.types import FederationTypeParams, TypeDefinition
from .utils.str_converters import to_camel_case


class StrawberryType:
    wrapped_class: Type

    def __init__(
        self,
        cls: Type,
        *,
        name: str,
        description: Optional[str] = None,
        is_input: bool = False,
        is_interface: bool = False,
        federation: Optional[FederationTypeParams] = None
    ):
        self.wrapped_class = dataclasses.dataclass(cls)
        self.name = name
        self.description = description
        self.is_input = is_input
        self.is_interface = is_interface
        self.federation = federation

    @property
    def fields(self) -> List[StrawberryField]:
        # Get fields defined in base classes
        inherited_fields: Dict[str, StrawberryField] = {}
        for base in self.wrapped_class.__bases__:
            if issubclass(StrawberryType, base):
                base = typing.cast(StrawberryType, base)
                # Add base's field definitions to cls' field definitions
                inherited_fields.update(**{f.name: f for f in base.fields})

        # Get fields defined dataclass-style (i.e. w/o strawberry.field)
        dataclass_fields: Dict[str, StrawberryField] = {}
        for field in dataclasses.fields(self.wrapped_class):
            field = typing.cast(dataclasses.Field, field)
            dataclass_fields[field.name] = StrawberryField(
                name=field.name, field_type=field.type
            )

        # Get fields defined using strawberry.field
        strawberry_fields: Dict[str, StrawberryField] = {}
        for field_name, field in self.__dict__.items():
            if isinstance(field, StrawberryField):
                # Grab name from class field, if necessary
                if field.name is None:
                    field.name = field_name

                # Check for duplicates
                if field.name in dataclass_fields or field.name in strawberry_fields:
                    # TODO: raise exception
                    ...

                strawberry_fields[field_name] = field

        # Aggregate all fields
        fields = {**inherited_fields, **dataclass_fields, **strawberry_fields}

        return list(fields.values())

    @property
    def interfaces(self) -> List["StrawberryType"]:
        interfaces = []
        for base in self.wrapped_class.__bases__:
            if not issubclass(StrawberryType, base):
                continue

            base = typing.cast(StrawberryType, base)
            if base.is_interface:
                interfaces.append(base)

        return interfaces

    def __call__(self, wrapped_class: Type):
        self.wrapped_class = wrapped_class

    def to_graphql_type(self) -> GraphQLObjectType:
        fields = list(map(StrawberryField.to_graphql_field, self.fields))
        interfaces = list(map(StrawberryType.to_graphql_type, self.interfaces))

        return GraphQLObjectType(
            name=self.name,
            fields=fields,
            description=self.description,
            interfaces=interfaces,
        )


def _get_interfaces(cls: Type) -> List[TypeDefinition]:
    interfaces = []

    for base in cls.__bases__:
        type_definition = cast(
            Optional[TypeDefinition], getattr(base, "_type_definition", None)
        )

        if type_definition and type_definition.is_interface:
            interfaces.append(type_definition)

    return interfaces


def _check_field_annotations(cls: Type):
    """Are any of the dataclass Fields missing type annotations?

    This replicates the check that dataclasses do during creation, but allows a
    proper Strawberry exception to be raised

    https://github.com/python/cpython/blob/6fed3c85402c5ca704eb3f3189ca3f5c67a08d19/Lib/dataclasses.py#L881-L884
    """
    cls_annotations = cls.__dict__.get("__annotations__", {})

    for field_name, value in cls.__dict__.items():
        if not isinstance(value, dataclasses.Field):
            # Not a dataclasses.Field. Ignore
            continue

        if field_name not in cls_annotations:
            # Field object exists but did not get an annotation
            raise MissingFieldAnnotationError(field_name)


def _wrap_dataclass(cls: Type):
    """Wrap a strawberry.type class with a dataclass and check for any issues
    before doing so"""

    # Ensure all Fields have been properly type-annotated
    _check_field_annotations(cls)

    return dataclasses.dataclass(cls)


def _process_type(
    cls,
    *,
    name: Optional[str] = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: Optional[str] = None,
    federation: Optional[FederationTypeParams] = None
):
    name = name or to_camel_case(cls.__name__)

    wrapped = _wrap_dataclass(cls)

    interfaces = _get_interfaces(wrapped)
    fields = _get_fields(cls)

    wrapped._type_definition = TypeDefinition(
        name=name,
        is_input=is_input,
        is_interface=is_interface,
        is_generic=is_generic(cls),
        interfaces=interfaces,
        description=description,
        federation=federation or FederationTypeParams(),
        origin=cls,
        _fields=fields,
    )

    return wrapped


def type(
    cls: Type = None,
    *,
    name: str = None,
    is_input: bool = False,
    is_interface: bool = False,
    description: str = None,
    federation: Optional[FederationTypeParams] = None
) -> StrawberryType:
    """Annotates a class as a GraphQL type.

    Example usage:

    >>> @strawberry.type:
    >>> class X:
    >>>     field_abc: str = "ABC"
    """

    return StrawberryType(
        cls=cls,
        name=name,
        description=description,
        is_input=is_input,
        is_interface=is_interface,
        federation=federation,
    )


input = partial(type, is_input=True)
interface = partial(type, is_interface=True)
