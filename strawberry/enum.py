import dataclasses
from enum import Enum, EnumMeta
from typing import Any, Callable, List, Mapping, Optional, TypeVar, Union

from typing_extensions import Annotated, get_args, get_origin

from strawberry.type import StrawberryType

from .exceptions import MultipleStrawberryEnumValuesError, NotAnEnum


@dataclasses.dataclass
class EnumValueAnnotation:
    description: Optional[str]


@dataclasses.dataclass
class EnumValue:
    name: str
    value: Any
    description: Optional[str]

    @classmethod
    def from_enum_item(cls, enum_cls: EnumMeta, item: Enum) -> "EnumValue":
        description = None
        try:
            annotation = enum_cls.__annotations__[item.name]
        except (AttributeError, KeyError):
            annotation = None

        if annotation is not None and get_origin(annotation) is Annotated:
            annotated_args = get_args(annotation)
            for arg in annotated_args[1:]:
                if isinstance(arg, EnumValueAnnotation):
                    if description is not None:
                        raise MultipleStrawberryEnumValuesError(
                            enum_class_name=enum_cls.__name__, enum_value_name=item.name
                        )

                    description = arg.description

        return cls(item.name, item.value, description)


@dataclasses.dataclass
class EnumDefinition(StrawberryType):
    wrapped_cls: EnumMeta
    name: str
    values: List[EnumValue]
    description: Optional[str]

    def __hash__(self) -> int:
        # TODO: Is this enough for unique-ness?
        return hash(self.name)

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        return super().copy_with(type_var_map)

    @property
    def is_generic(self) -> bool:
        return False


def _process_enum(
    cls: EnumMeta, name: Optional[str] = None, description: Optional[str] = None
) -> EnumMeta:
    if not isinstance(cls, EnumMeta):
        raise NotAnEnum()

    if not name:
        name = cls.__name__

    description = description

    values = [EnumValue.from_enum_item(cls, item) for item in cls]  # type: ignore

    cls._enum_definition = EnumDefinition(  # type: ignore
        wrapped_cls=cls,
        name=name,
        values=values,
        description=description,
    )

    return cls


def enum(
    _cls: EnumMeta = None, *, name=None, description=None
) -> Union[EnumMeta, Callable[[EnumMeta], EnumMeta]]:
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    def wrap(cls: EnumMeta) -> EnumMeta:
        return _process_enum(cls, name, description)

    if not _cls:
        return wrap

    return wrap(_cls)


def enum_value(description: Optional[str] = None):
    return EnumValueAnnotation(description=description)
