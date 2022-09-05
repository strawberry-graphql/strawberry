import contextlib
import dataclasses
import inspect
import sys
from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Iterable,
    NewType,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
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


# TODO: Maybe rename this to StrawberryScalar?
@dataclass
class ScalarDefinition(StrawberryType):
    origin: Optional[type] = None
    name: str = None
    description: Optional[str] = None
    specified_by_url: Optional[str] = None
    serialize: Optional[Callable] = None
    parse_value: Optional[Callable] = None
    parse_literal: Optional[Callable] = None
    directives: Iterable[object] = ()

    # Optionally store the GraphQLScalarType instance so that we don't get
    # duplicates
    implementation: Optional[GraphQLScalarType] = None

    def to_graphql_core(self):
        if self.implementation:
            return self.implementation
        else:
            from strawberry.schema.schema_converter import GraphQLCoreConverter

            res = GraphQLScalarType(
                name=self.name,
                description=self.description,
                specified_by_url=self.specified_by_url,
                serialize=self.serialize,
                parse_value=self.parse_value,
                parse_literal=self.parse_literal,
                extensions={GraphQLCoreConverter.DEFINITION_BACKREF: self},
            )
            # cache
            self.implementation = res
            self.implementation = cast(GraphQLScalarType, res)
            return self.implementation

    def __call__(self, class_or_value: Any = None):
        if (
            inspect.isclass(class_or_value)
            or type(class_or_value) is NewType
            and not self.origin
        ):
            self.origin = class_or_value
            if not self.name:
                return dataclasses.replace(
                    self, name=to_camel_case(class_or_value.__name__)
                )
            return self
        elif class_or_value:
            # if someone tries to `initialize` the scalar just return what he gave
            # parse_value will be called else where.
            return class_or_value
        else:
            # ugly fix for `test_custom_scalar_decorated_class`
            return self.serialize(None)

    @property
    def is_generic(self) -> bool:
        return False

    def _validate(self, value):
        with contextlib.suppress(Exception):
            parsed = self.parse_value(value)
            if self.serialize(parsed) == value:
                return True
        with contextlib.suppress(Exception):
            serialized = self.serialize(value)
            if self.parse_value(serialized) == value:
                return True
        return False

    def __hash__(self) -> int:
        return id(self)


def scalar(
    cls: Type = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    specified_by_url: Optional[str] = None,
    serialize: Optional[Callable] = None,
    parse_value: Optional[Callable] = None,
    parse_literal: Optional[Callable] = None,
    directives: Iterable[object] = (),
) -> ScalarDefinition:
    definition = ScalarDefinition(
        name=name,
        description=description,
        specified_by_url=specified_by_url,
        serialize=serialize,
        parse_literal=parse_literal,
        parse_value=parse_value,
        directives=directives,
    )
    if cls:
        return definition(cls)

    return definition
