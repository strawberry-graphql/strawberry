import sys
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Mapping,
    NewType,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from graphql import GraphQLScalarType

from strawberry.type import StrawberryType

from .utils.str_converters import to_camel_case


# in python 3.10+ NewType is a class
if sys.version_info >= (3, 10):
    _T = TypeVar("_T", bound=Union[type, NewType])
else:
    _T = TypeVar("_T", bound=type)


def identity(x):
    return x


@dataclass
class ScalarDefinition(StrawberryType):
    name: str
    description: Optional[str]
    specified_by_url: Optional[str]
    serialize: Optional[Callable]
    parse_value: Optional[Callable]
    parse_literal: Optional[Callable]

    # Optionally store the GraphQLScalarType instance so that we don't get
    # duplicates
    implementation: Optional[GraphQLScalarType] = None

    def copy_with(
        self, type_var_map: Mapping[TypeVar, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        return super().copy_with(type_var_map)

    @property
    def is_generic(self) -> bool:
        return False


class ScalarWrapper:
    _scalar_definition: ScalarDefinition

    def __init__(self, wrap):
        self.wrap = wrap

    def __call__(self, *args, **kwargs):
        return self.wrap(*args, **kwargs)


def _process_scalar(
    cls: Type[_T],
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    specified_by_url: Optional[str] = None,
    serialize: Optional[Callable] = None,
    parse_value: Optional[Callable] = None,
    parse_literal: Optional[Callable] = None,
):
    name = name or to_camel_case(cls.__name__)

    wrapper = ScalarWrapper(cls)
    wrapper._scalar_definition = ScalarDefinition(
        name=name,
        description=description,
        specified_by_url=specified_by_url,
        serialize=serialize,
        parse_literal=parse_literal,
        parse_value=parse_value,
    )

    return wrapper


@overload
def scalar(
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    specified_by_url: Optional[str] = None,
    serialize: Callable = identity,
    parse_value: Optional[Callable] = None,
    parse_literal: Optional[Callable] = None,
) -> Callable[[_T], _T]:
    ...


@overload
def scalar(
    cls: _T,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    specified_by_url: Optional[str] = None,
    serialize: Callable = identity,
    parse_value: Optional[Callable] = None,
    parse_literal: Optional[Callable] = None,
) -> _T:
    ...


# FIXME: We are tricking pyright into thinking that we are returning the given type
# here or else it won't let us use any custom scalar to annotate attributes in
# dataclasses/types. This should be properly solved when implementing StrawberryScalar
def scalar(
    cls=None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    specified_by_url: Optional[str] = None,
    serialize: Callable = identity,
    parse_value: Optional[Callable] = None,
    parse_literal: Optional[Callable] = None,
) -> Any:
    """Annotates a class or type as a GraphQL custom scalar.

    Example usages:

    >>> strawberry.scalar(
    >>>     datetime.date,
    >>>     serialize=lambda value: value.isoformat(),
    >>>     parse_value=datetime.parse_date
    >>> )

    >>> Base64Encoded = strawberry.scalar(
    >>>     NewType("Base64Encoded", bytes),
    >>>     serialize=base64.b64encode,
    >>>     parse_value=base64.b64decode
    >>> )

    >>> @strawberry.scalar(
    >>>     serialize=lambda value: ",".join(value.items),
    >>>     parse_value=lambda value: CustomList(value.split(","))
    >>> )
    >>> class CustomList:
    >>>     def __init__(self, items):
    >>>         self.items = items

    """

    if parse_value is None:
        parse_value = cls

    def wrap(cls):
        return _process_scalar(
            cls,
            name=name,
            description=description,
            specified_by_url=specified_by_url,
            serialize=serialize,
            parse_value=parse_value,
            parse_literal=parse_literal,
        )

    if cls is None:
        return wrap

    return wrap(cls)
