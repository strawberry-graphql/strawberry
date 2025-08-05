import dataclasses
from collections.abc import Iterable, Mapping
from enum import EnumMeta
from typing import (
    Any,
    Callable,
    Optional,
    TypeVar,
    Union,
    overload,
)

from strawberry.exceptions import ObjectIsNotAnEnumError
from strawberry.types.base import StrawberryType


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
    values: list[EnumValue]
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

    @property
    def origin(self) -> type:
        return self.wrapped_cls


# TODO: remove duplication of EnumValueDefinition and EnumValue
@dataclasses.dataclass
class EnumValueDefinition:
    value: Any
    graphql_name: Optional[str] = None
    deprecation_reason: Optional[str] = None
    directives: Iterable[object] = ()
    description: Optional[str] = None

    def __int__(self) -> int:
        return self.value


def enum_value(
    value: Any,
    name: Optional[str] = None,
    deprecation_reason: Optional[str] = None,
    directives: Iterable[object] = (),
    description: Optional[str] = None,
) -> EnumValueDefinition:
    """Function to customise an enum value, for example to add a description or deprecation reason.

    Args:
        value: The value of the enum member.
        name: The GraphQL name of the enum member.
        deprecation_reason: The deprecation reason of the enum member,
            setting this will mark the enum member as deprecated.
        directives: The directives to attach to the enum member.
        description: The GraphQL description of the enum member.

    Returns:
        An EnumValueDefinition object that can be used to customise an enum member.

    Example:
    ```python
    from enum import Enum
    import strawberry


    @strawberry.enum
    class MyEnum(Enum):
        FIRST_VALUE = strawberry.enum_value(description="The first value")
        SECOND_VALUE = strawberry.enum_value(description="The second value")
    ```
    """
    return EnumValueDefinition(
        value=value,
        graphql_name=name,
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

            # update _value2member_map_ so that doing `MyEnum.MY_VALUE` and
            # `MyEnum['MY_VALUE']` both work
            cls._value2member_map_[item_value.value] = item
            cls._member_map_[item_name]._value_ = item_value.value

            if item_value.graphql_name:
                item_name = item_value.graphql_name

            item_value = item_value.value

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
    cls: EnumType,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> EnumType: ...


@overload
def enum(
    cls: None = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> Callable[[EnumType], EnumType]: ...


def enum(
    cls: Optional[EnumType] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> Union[EnumType, Callable[[EnumType], EnumType]]:
    """Annotates an Enum class a GraphQL enum.

    GraphQL enums only have names, while Python enums have names and values,
    Strawberry will use the names of the Python enum as the names of the
    GraphQL enum values.

    Args:
        cls: The Enum class to be annotated.
        name: The name of the GraphQL enum.
        description: The description of the GraphQL enum.
        directives: The directives to attach to the GraphQL enum.

    Returns:
        The decorated Enum class.

    Example:
    ```python
    from enum import Enum
    import strawberry


    @strawberry.enum
    class MyEnum(Enum):
        FIRST_VALUE = "first_value"
        SECOND_VALUE = "second_value"
    ```

    The above code will generate the following GraphQL schema:

    ```graphql
    enum MyEnum {
        FIRST_VALUE
        SECOND_VALUE
    }
    ```

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    def wrap(cls: EnumType) -> EnumType:
        return _process_enum(cls, name, description, directives=directives)

    if not cls:
        return wrap

    return wrap(cls)


__all__ = ["EnumDefinition", "EnumValue", "EnumValueDefinition", "enum", "enum_value"]
