import dataclasses
from collections.abc import Callable, Iterable, Mapping
from enum import EnumMeta
from typing import TYPE_CHECKING, Any, Literal, TypeGuard, TypeVar, overload

from strawberry.exceptions import ObjectIsNotAnEnumError
from strawberry.types.base import (
    StrawberryType,
    WithStrawberryDefinition,
    has_strawberry_definition,
)
from strawberry.utils.deprecations import DEPRECATION_MESSAGES, DeprecatedDescriptor


@dataclasses.dataclass
class EnumValue:
    name: str
    value: Any
    deprecation_reason: str | None = None
    directives: Iterable[object] = ()
    description: str | None = None


@dataclasses.dataclass
class StrawberryEnumDefinition(StrawberryType):
    wrapped_cls: EnumMeta
    name: str
    values: list[EnumValue]
    description: str | None
    directives: Iterable[object] = ()

    def __hash__(self) -> int:
        # TODO: Is this enough for unique-ness?
        return hash(self.name)

    def copy_with(
        self, type_var_map: Mapping[str, StrawberryType | type]
    ) -> StrawberryType | type:
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
    graphql_name: str | None = None
    deprecation_reason: str | None = None
    directives: Iterable[object] = ()
    description: str | None = None

    def __int__(self) -> int:
        return self.value


def enum_value(
    value: Any,
    name: str | None = None,
    deprecation_reason: str | None = None,
    directives: Iterable[object] = (),
    description: str | None = None,
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
GraphqlEnumNameFrom = Literal["key", "value"]


def _process_enum(
    cls: EnumType,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    graphql_name_from: GraphqlEnumNameFrom = "key",
) -> EnumType:
    if not isinstance(cls, EnumMeta):
        raise ObjectIsNotAnEnumError(cls)

    if not name:
        name = cls.__name__

    values = []
    for item in cls:  # type: ignore
        graphql_name = None
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

            graphql_name = item_value.graphql_name
            item_value = item_value.value

        if not graphql_name:
            if graphql_name_from == "key":
                graphql_name = item_name
            elif graphql_name_from == "value":
                graphql_name = item_value
            else:
                raise ValueError(f"Invalid mode: {graphql_name_from}")

        value = EnumValue(
            graphql_name,
            item_value,
            deprecation_reason=deprecation_reason,
            directives=item_directives,
            description=enum_value_description,
        )
        values.append(value)

    cls.__strawberry_definition__ = StrawberryEnumDefinition(  # type: ignore
        wrapped_cls=cls,
        name=name,
        values=values,
        description=description,
        directives=directives,
    )

    # TODO: remove when deprecating _enum_definition
    DeprecatedDescriptor(
        DEPRECATION_MESSAGES._ENUM_DEFINITION,
        cls.__strawberry_definition__,  # type: ignore[attr-defined]
        "_enum_definition",
    ).inject(cls)

    return cls


@overload
def enum(
    cls: EnumType,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    graphql_name_from: GraphqlEnumNameFrom = "key",
) -> EnumType: ...


@overload
def enum(
    cls: None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    graphql_name_from: GraphqlEnumNameFrom = "key",
) -> Callable[[EnumType], EnumType]: ...


def enum(
    cls: EnumType | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    directives: Iterable[object] = (),
    graphql_name_from: GraphqlEnumNameFrom = "key",
) -> EnumType | Callable[[EnumType], EnumType]:
    """Annotates an Enum class a GraphQL enum.

    GraphQL enums only have names, while Python enums have names and values,
    Strawberry will by default use the names of the Python enum as the names of the
    GraphQL enum values. You can use the values instead by using mode="value".

    Args:
        cls: The Enum class to be annotated.
        name: The name of the GraphQL enum.
        description: The description of the GraphQL enum.
        directives: The directives to attach to the GraphQL enum.
        graphql_name_from: Whether to use the names (key) or values of the Python enums in GraphQL.

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
        return _process_enum(
            cls,
            name,
            description,
            directives=directives,
            graphql_name_from=graphql_name_from,
        )

    if not cls:
        return wrap

    return wrap(cls)


# TODO: remove when deprecating _enum_definition
if TYPE_CHECKING:
    from typing_extensions import deprecated

    @deprecated("Use StrawberryEnumDefinition instead")
    class EnumDefinition(StrawberryEnumDefinition): ...

else:
    EnumDefinition = StrawberryEnumDefinition

WithStrawberryEnumDefinition = WithStrawberryDefinition["StrawberryEnumDefinition"]


def has_enum_definition(obj: Any) -> TypeGuard[type[WithStrawberryEnumDefinition]]:
    if has_strawberry_definition(obj):
        return isinstance(obj.__strawberry_definition__, StrawberryEnumDefinition)

    return False


__all__ = [
    "EnumDefinition",
    "EnumValue",
    "EnumValueDefinition",
    "StrawberryEnumDefinition",
    "enum",
    "enum_value",
]
