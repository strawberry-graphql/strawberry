import dataclasses
from enum import EnumMeta
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Mapping,
    Optional,
    TypeVar,
    Union,
    overload,
)

from strawberry.description_sources import DescriptionSources
from strawberry.exceptions import ObjectIsNotAnEnumError
from strawberry.type import StrawberryType
from strawberry.utils.docstrings import Docstring


@dataclasses.dataclass
class EnumValue:
    name: str
    value: Any
    deprecation_reason: Optional[str] = None
    directives: Iterable[object] = ()
    description_sources: Optional[DescriptionSources] = None
    description: Optional[str] = None


@dataclasses.dataclass
class EnumDefinition(StrawberryType):
    wrapped_cls: EnumMeta
    name: str
    values: List[EnumValue]
    description_sources: Optional[DescriptionSources] = None
    description: Optional[str] = None
    docstring: Optional[Docstring] = None
    directives: Iterable[object] = ()

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


# TODO: remove duplication of EnumValueDefinition and EnumValue
@dataclasses.dataclass
class EnumValueDefinition:
    value: Any
    deprecation_reason: Optional[str] = None
    directives: Iterable[object] = ()
    description_sources: Optional[DescriptionSources] = None
    description: Optional[str] = None


def enum_value(
    value: Any,
    *,
    description_sources: Optional[DescriptionSources] = None,
    description: Optional[str] = None,
    deprecation_reason: Optional[str] = None,
    directives: Iterable[object] = (),
) -> EnumValueDefinition:
    return EnumValueDefinition(
        value=value,
        description_sources=description_sources,
        description=description,
        deprecation_reason=deprecation_reason,
        directives=directives,
    )


EnumType = TypeVar("EnumType", bound=EnumMeta)


def _process_enum(
    cls: EnumType,
    name: Optional[str] = None,
    description_sources: Optional[DescriptionSources] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> EnumType:
    if not isinstance(cls, EnumMeta):
        raise ObjectIsNotAnEnumError(cls)

    if not name:
        name = cls.__name__

    values = []
    for item in cls:  # type: ignore
        item_value = item.value
        item_name = item.name
        item_description_sources = None
        item_deprecation_reason = None
        item_directives: Iterable[object] = ()
        item_description = None

        if isinstance(item_value, EnumValueDefinition):
            item_directives = item_value.directives
            item_description_sources = item_value.description_sources
            item_description = item_value.description
            item_deprecation_reason = item_value.deprecation_reason
            item_value = item_value.value

        value = EnumValue(
            item_name,
            item_value,
            deprecation_reason=item_deprecation_reason,
            directives=item_directives,
            description_sources=item_description_sources,
            description=item_description,
        )
        values.append(value)

    cls._enum_definition = EnumDefinition(  # type: ignore
        wrapped_cls=cls,
        name=name,
        values=values,
        description_sources=description_sources,
        description=description,
        docstring=Docstring(cls),
        directives=directives,
    )

    return cls


@overload
def enum(
    _cls: EnumType,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> EnumType:
    ...


@overload
def enum(
    _cls: None = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> Callable[[EnumType], EnumType]:
    ...


def enum(
    _cls: Optional[EnumType] = None,
    *,
    name: Optional[str] = None,
    description_sources: Optional[DescriptionSources] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> Union[EnumType, Callable[[EnumType], EnumType]]:
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    def wrap(cls: EnumType) -> EnumType:
        return _process_enum(
            cls,
            name,
            description_sources=description_sources,
            description=description,
            directives=directives,
        )

    if not _cls:
        return wrap

    return wrap(_cls)
