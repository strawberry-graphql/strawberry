from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Iterable,
    Mapping,
    NewType,
    Optional,
    TypeVar,
    Union,
    overload,
)

from strawberry.exceptions import InvalidUnionTypeError
from strawberry.types.base import StrawberryType
from strawberry.utils.str_converters import to_camel_case

if TYPE_CHECKING:
    from graphql import GraphQLScalarType


# in python 3.10+ NewType is a class
if sys.version_info >= (3, 10):
    _T = TypeVar("_T", bound=Union[type, NewType])
else:
    _T = TypeVar("_T", bound=type)


def identity(x: _T) -> _T:
    return x


@dataclass
class ScalarDefinition(StrawberryType):
    name: str
    description: Optional[str]
    specified_by_url: Optional[str]
    serialize: Optional[Callable]
    parse_value: Optional[Callable]
    parse_literal: Optional[Callable]
    directives: Iterable[object] = ()

    # Optionally store the GraphQLScalarType instance so that we don't get
    # duplicates
    implementation: Optional[GraphQLScalarType] = None

    # used for better error messages
    _source_file: Optional[str] = None
    _source_line: Optional[int] = None

    def copy_with(
        self, type_var_map: Mapping[str, Union[StrawberryType, type]]
    ) -> Union[StrawberryType, type]:
        return super().copy_with(type_var_map)  # type: ignore[safe-super]

    @property
    def is_graphql_generic(self) -> bool:
        return False


class ScalarWrapper:
    _scalar_definition: ScalarDefinition

    def __init__(self, wrap: Callable[[Any], Any]) -> None:
        self.wrap = wrap

    def __call__(self, *args: str, **kwargs: Any) -> Any:
        return self.wrap(*args, **kwargs)

    def __or__(self, other: Union[StrawberryType, type]) -> StrawberryType:
        if other is None:
            # Return the correct notation when using `StrawberryUnion | None`.
            return Optional[self]

        # Raise an error in any other case.
        # There is Work in progress to deal with more merging cases, see:
        # https://github.com/strawberry-graphql/strawberry/pull/1455
        raise InvalidUnionTypeError(str(other), self.wrap)


def _process_scalar(
    cls: _T,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    specified_by_url: Optional[str] = None,
    serialize: Optional[Callable] = None,
    parse_value: Optional[Callable] = None,
    parse_literal: Optional[Callable] = None,
    directives: Iterable[object] = (),
) -> ScalarWrapper:
    from strawberry.exceptions.handler import should_use_rich_exceptions

    name = name or to_camel_case(cls.__name__)  # type: ignore[union-attr]

    _source_file = None
    _source_line = None

    if should_use_rich_exceptions():
        frame = sys._getframe(3)

        _source_file = frame.f_code.co_filename
        _source_line = frame.f_lineno

    wrapper = ScalarWrapper(cls)
    wrapper._scalar_definition = ScalarDefinition(
        name=name,
        description=description,
        specified_by_url=specified_by_url,
        serialize=serialize,
        parse_literal=parse_literal,
        parse_value=parse_value,
        directives=directives,
        _source_file=_source_file,
        _source_line=_source_line,
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
    directives: Iterable[object] = (),
) -> Callable[[_T], _T]: ...


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
    directives: Iterable[object] = (),
) -> _T: ...


# TODO: We are tricking pyright into thinking that we are returning the given type
# here or else it won't let us use any custom scalar to annotate attributes in
# dataclasses/types. This should be properly solved when implementing StrawberryScalar
def scalar(
    cls: Optional[_T] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    specified_by_url: Optional[str] = None,
    serialize: Callable = identity,
    parse_value: Optional[Callable] = None,
    parse_literal: Optional[Callable] = None,
    directives: Iterable[object] = (),
) -> Any:
    """Annotates a class or type as a GraphQL custom scalar.

    Args:
        cls: The class or type to annotate.
        name: The GraphQL name of the scalar.
        description: The description of the scalar.
        specified_by_url: The URL of the specification.
        serialize: The function to serialize the scalar.
        parse_value: The function to parse the value.
        parse_literal: The function to parse the literal.
        directives: The directives to apply to the scalar.

    Returns:
        The decorated class or type.

    Example usages:

    ```python
    strawberry.scalar(
        datetime.date,
        serialize=lambda value: value.isoformat(),
        parse_value=datetime.parse_date,
    )

    Base64Encoded = strawberry.scalar(
        NewType("Base64Encoded", bytes),
        serialize=base64.b64encode,
        parse_value=base64.b64decode,
    )


    @strawberry.scalar(
        serialize=lambda value: ",".join(value.items),
        parse_value=lambda value: CustomList(value.split(",")),
    )
    class CustomList:
        def __init__(self, items):
            self.items = items
    ```
    """
    if parse_value is None:
        parse_value = cls

    def wrap(cls: _T) -> ScalarWrapper:
        return _process_scalar(
            cls,
            name=name,
            description=description,
            specified_by_url=specified_by_url,
            serialize=serialize,
            parse_value=parse_value,
            parse_literal=parse_literal,
            directives=directives,
        )

    if cls is None:
        return wrap

    return wrap(cls)


__all__ = ["ScalarDefinition", "ScalarWrapper", "scalar"]
