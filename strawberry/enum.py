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

from strawberry.type import StrawberryType

from .exceptions import ObjectIsNotAnEnumError


@dataclasses.dataclass
class EnumValue:
    name: str
    value: Any
    deprecation_reason: Optional[str] = None
    directives: Iterable[object] = ()
    description: Optional[str] = None


@dataclasses.dataclass
class EnumDefinition(StrawberryType):
    wrapped_cls: EnumMeta
    name: str
    values: List[EnumValue]
    description: Optional[str]
    directives: Iterable[object] = ()

    def __hash__(self) -> int:
        # TODO: Is this enough for unique-ness?
        return hash(self.name)

    def copy_with(
        self, type_var_map: Mapping[str, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        # enum don't support type parameters, so we can safely return self
        return self

    @property
    def is_graphql_generic(self) -> bool:
        return False


# TODO: remove duplication of EnumValueDefinition and EnumValue
@dataclasses.dataclass
class EnumValueDefinition:
    value: Any
    deprecation_reason: Optional[str] = None
    directives: Iterable[object] = ()
    description: Optional[str] = None

    def __int__(self) -> int:
        return self.value


def enum_value(
    value: Any,
    deprecation_reason: Optional[str] = None,
    directives: Iterable[object] = (),
    description: Optional[str] = None,
) -> EnumValueDefinition:
    return EnumValueDefinition(
        value=value,
        deprecation_reason=deprecation_reason,
        directives=directives,
        description=description,
    )


EnumType = TypeVar("EnumType", bound=EnumMeta)


def _process_enum(
    cls: EnumType,
    name: Optional[str] = None,
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
        deprecation_reason = None
        item_directives: Iterable[object] = ()
        enum_value_description = None

        if isinstance(item_value, EnumValueDefinition):
            item_directives = item_value.directives
            enum_value_description = item_value.description
            deprecation_reason = item_value.deprecation_reason
            item_value = item_value.value

            # update _value2member_map_ so that doing `MyEnum.MY_VALUE` and
            # `MyEnum['MY_VALUE']` both work
            cls._value2member_map_[item_value] = item
            cls._member_map_[item_name]._value_ = item_value

        value = EnumValue(
            item_name,
            item_value,
            deprecation_reason=deprecation_reason,
            directives=item_directives,
            description=enum_value_description,
        )
        values.append(value)

    cls._enum_definition = EnumDefinition(  # type: ignore
        wrapped_cls=cls,
        name=name,
        values=values,
        description=description,
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
) -> EnumType: ...


@overload
def enum(
    _cls: None = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> Callable[[EnumType], EnumType]: ...


def enum(
    _cls: Optional[EnumType] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> Union[EnumType, Callable[[EnumType], EnumType]]:
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    def wrap(cls: EnumType) -> EnumType:
        return _process_enum(cls, name, description, directives=directives)

    if not _cls:
        return wrap

    return wrap(_cls)
