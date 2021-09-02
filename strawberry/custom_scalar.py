from dataclasses import dataclass
from typing import Callable, Mapping, Optional, TypeVar, Union

from graphql import GraphQLScalarType

from strawberry.type import StrawberryType

from .utils.str_converters import to_camel_case


def identity(x):
    return x


@dataclass
class ScalarDefinition(StrawberryType):
    name: str
    description: Optional[str]
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
    cls,
    *,
    name: str = None,
    description: str = None,
    serialize: Callable = None,
    parse_value: Callable = None,
    parse_literal: Callable = None
):

    name = name or to_camel_case(cls.__name__)

    wrapper = ScalarWrapper(cls)
    wrapper._scalar_definition = ScalarDefinition(
        name=name,
        description=description,
        serialize=serialize,
        parse_literal=parse_literal,
        parse_value=parse_value,
    )

    return wrapper


def scalar(
    cls=None,
    *,
    name: str = None,
    description: str = None,
    serialize: Callable = identity,
    parse_value: Optional[Callable] = None,
    parse_literal: Optional[Callable] = None
):
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
            serialize=serialize,
            parse_value=parse_value,
            parse_literal=parse_literal,
        )

    if cls is None:
        return wrap

    return wrap(cls)
