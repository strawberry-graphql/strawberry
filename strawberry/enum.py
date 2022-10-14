import dataclasses
from enum import Enum, EnumMeta
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
    description: Optional[str] = None


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


class StrawberryEnumMeta(EnumMeta):
    def __new__(
        metacls,
        cls,
        bases,
        classdict,
        name: Optional[str] = None,
        description: Optional[str] = None,
        directives: Iterable[object] = (),
        **kwds,
    ):
        enum_class = EnumMeta.__new__(metacls, cls, bases, classdict, **kwds)
        setattr(enum_class, "_name", name)
        setattr(enum_class, "_description", description)
        setattr(enum_class, "_directives", directives)
        values = []
        for item in enum_class.__members__.values():  # type: ignore

            value = EnumValue(
                item.name,
                item.value,
                deprecation_reason=item.deprecation_reason,
                directives=item.directives,
                description=item.description,
            )
            values.append(value)
        enum_class._enum_definition = EnumDefinition(  # type: ignore
            wrapped_cls=enum_class,
            name=enum_class._name or enum_class.__name__,
            values=values,
            description=enum_class._description,
            directives=enum_class._directives,
        )

        return enum_class


def _default_adapt_fn(item):
    if isinstance(item, Enum):
        return {
            "value": item,
            "description": getattr(item, "description", None),
            "deprecation_reason": getattr(item, "deprecation_reason", None),
            "directives": getattr(item, "directives", None),
        }
    else:
        return {
            "description": getattr(item, "_description", None),
            "deprecation_reason": getattr(item, "_deprecation_reason", None),
            "directives": getattr(item, "_directives", None),
        }


class StrawberryEnum(Enum, metaclass=StrawberryEnumMeta):
    def __new__(
        cls,
        value: Any = None,
    ):
        item_value = value
        deprecation_reason = None
        directives: Iterable[object] = ()
        description = None
        if isinstance(item_value, EnumValueDefinition):
            description = item_value.description
            deprecation_reason = item_value.deprecation_reason
            directives = item_value.directives
            item_value = item_value.value
        obj = object.__new__(cls)
        obj._value_ = item_value
        obj.description = description
        obj.deprecation_reason = deprecation_reason
        obj.directives = directives
        return obj

    def __call__(
        cls,
        value,
        names=None,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        directives: Iterable[object] = (),
        module=None,
        qualname=None,
        type=None,
        start=1,
    ):
        enum_class = Enum.__call__(
            cls,
            names,
            module=module,
            qualname=qualname,
            type=type,
            start=start,
        )
        if names:
            if name:
                setattr(enum_class, "_name", name)
            if description:
                setattr(enum_class, "_description", description)
            if directives:
                setattr(enum_class, "_directives", directives)

            values = []
            for item in enum_class:  # type: ignore

                value = EnumValue(
                    item.name,
                    item.value,
                    deprecation_reason=item.deprecation_reason,
                    directives=item.directives,
                    description=item.description,
                )
                values.append(value)
            enum_class._enum_definition = EnumDefinition(  # type: ignore
                wrapped_cls=enum_class,
                name=enum_class._name or enum_class.__name__,
                values=values,
                description=enum_class._description,
                directives=enum_class._directives,
            )
        return enum_class

    @classmethod
    def adapt(cls, enum, adapt_fn=None):
        if not isinstance(enum, EnumMeta):
            raise ObjectIsNotAnEnumError(enum)
        if not adapt_fn:
            adapt_fn = _default_adapt_fn
        basedef = adapt_fn(enum)
        return cls(
            basedef.get("name", enum.__name__),
            map(
                lambda name, value_enum: (
                    name,
                    EnumValueDefinition(**adapt_fn(value_enum)),
                ),
                enum.__members__.items(),
            ),
        )


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
    description: Optional[str] = None,
    directives: Iterable[object] = (),
) -> Union[EnumType, Callable[[EnumType], EnumType]]:
    """Registers the enum in the GraphQL type system.

    If name is passed, the name of the GraphQL type will be
    the value passed of name instead of the Enum class name.
    """

    def wrap(cls: EnumType) -> EnumType:
        def adapt_fn(item):
            if isinstance(item, Enum):
                return _default_adapt_fn(item)
            else:
                return {
                    "name": name,
                    "description": description,
                    "directives": directives,
                }

        return StrawberryEnum.adapt(cls, adapt_fn=adapt_fn)

    if not _cls:
        return wrap

    return wrap(_cls)
