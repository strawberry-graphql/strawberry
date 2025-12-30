from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    NewType,
    Optional,
    TypeVar,
    overload,
)

from strawberry.exceptions import InvalidUnionTypeError
from strawberry.types.base import StrawberryType
from strawberry.utils.str_converters import to_camel_case

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from graphql import GraphQLScalarType


_T = TypeVar("_T", bound=type | NewType)


def identity(x: _T) -> _T:
    return x


@dataclass
class ScalarDefinition(StrawberryType):
    name: str
    description: str | None
    specified_by_url: str | None
    serialize: Callable | None
    parse_value: Callable | None
    parse_literal: Callable | None
    directives: Iterable[object] = ()
    origin: GraphQLScalarType | type | None = None

    # Optionally store the GraphQLScalarType instance so that we don't get
    # duplicates
    implementation: GraphQLScalarType | None = None

    # used for better error messages
    _source_file: str | None = None
    _source_line: int | None = None

    def copy_with(
        self, type_var_map: Mapping[str, StrawberryType | type]
    ) -> StrawberryType | type:
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

    def __or__(self, other: StrawberryType | type) -> StrawberryType:
        if other is None:
            # Return the correct notation when using `StrawberryUnion | None`.
            return Optional[self]  # noqa: UP045

        # Raise an error in any other case.
        # There is Work in progress to deal with more merging cases, see:
        # https://github.com/strawberry-graphql/strawberry/pull/1455
        raise InvalidUnionTypeError(str(other), self.wrap)


def _process_scalar(
    cls: _T,
    *,
    name: str | None = None,
    description: str | None = None,
    specified_by_url: str | None = None,
    serialize: Callable | None = None,
    parse_value: Callable | None = None,
    parse_literal: Callable | None = None,
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
        origin=cls,  # type: ignore[arg-type]
        _source_file=_source_file,
        _source_line=_source_line,
    )

    return wrapper


@overload
def scalar(
    cls: None = None,
    *,
    name: str,
    description: str | None = None,
    specified_by_url: str | None = None,
    serialize: Callable = identity,
    parse_value: Callable | None = None,
    parse_literal: Callable | None = None,
    directives: Iterable[object] = (),
) -> ScalarDefinition: ...


@overload
def scalar(
    cls: None = None,
    *,
    name: None = None,
    description: str | None = None,
    specified_by_url: str | None = None,
    serialize: Callable = identity,
    parse_value: Callable | None = None,
    parse_literal: Callable | None = None,
    directives: Iterable[object] = (),
) -> Callable[[_T], _T]: ...


@overload
def scalar(
    cls: _T,
    *,
    name: str | None = None,
    description: str | None = None,
    specified_by_url: str | None = None,
    serialize: Callable = identity,
    parse_value: Callable | None = None,
    parse_literal: Callable | None = None,
    directives: Iterable[object] = (),
) -> _T: ...


# TODO: We are tricking pyright into thinking that we are returning the given type
# here or else it won't let us use any custom scalar to annotate attributes in
# dataclasses/types. This should be properly solved when implementing StrawberryScalar
def scalar(
    cls: _T | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    specified_by_url: str | None = None,
    serialize: Callable = identity,
    parse_value: Callable | None = None,
    parse_literal: Callable | None = None,
    directives: Iterable[object] = (),
) -> Any:
    """Annotates a class or type as a GraphQL custom scalar.

    This function can be used in three ways:

    1. With a `name` but no `cls`: Returns a `ScalarDefinition` for use in
       `StrawberryConfig.scalar_map`. This is the recommended approach as it
       provides proper type checking support.

    2. As a decorator (no `cls`): Returns a decorator function. When the `cls`
       argument is provided inline, this is deprecated in favor of using
       `scalar_map`.

    3. With a `cls` argument (deprecated): Wraps the class/type directly.
       This approach is deprecated because it causes type checker issues.
       Use `scalar_map` in `StrawberryConfig` instead.

    Args:
        cls: The class or type to annotate (deprecated, use scalar_map instead).
        name: The GraphQL name of the scalar.
        description: The description of the scalar.
        specified_by_url: The URL of the specification.
        serialize: The function to serialize the scalar.
        parse_value: The function to parse the value.
        parse_literal: The function to parse the literal.
        directives: The directives to apply to the scalar.

    Returns:
        A `ScalarDefinition` when called with `name` only, a decorator function
        when called without arguments, or the wrapped type when called with `cls`.

    Example usages:

    Recommended approach using scalar_map:

    ```python
    from typing import NewType
    import strawberry
    from strawberry.schema.config import StrawberryConfig

    # Define the type
    Base64 = NewType("Base64", bytes)

    # Configure the scalar in schema config
    schema = strawberry.Schema(
        query=Query,
        config=StrawberryConfig(
            scalar_map={
                Base64: strawberry.scalar(
                    name="Base64",
                    serialize=lambda v: base64.b64encode(v).decode(),
                    parse_value=lambda v: base64.b64decode(v),
                )
            }
        ),
    )
    ```

    Legacy approach (deprecated):

    ```python
    Base64Encoded = strawberry.scalar(
        NewType("Base64Encoded", bytes),
        serialize=base64.b64encode,
        parse_value=base64.b64decode,
    )
    ```
    """
    from strawberry.exceptions.handler import should_use_rich_exceptions

    _source_file = None
    _source_line = None

    if should_use_rich_exceptions():
        frame = sys._getframe(1)
        _source_file = frame.f_code.co_filename
        _source_line = frame.f_lineno

    if cls is None and name is not None:
        return ScalarDefinition(
            name=name,
            description=description,
            specified_by_url=specified_by_url,
            serialize=serialize,
            parse_literal=parse_literal,
            parse_value=parse_value,
            directives=directives,
            origin=None,
            _source_file=_source_file,
            _source_line=_source_line,
        )

    if parse_value is None:
        parse_value = cls

    def wrap(cls: _T) -> ScalarWrapper:
        import warnings

        warnings.warn(
            "Passing a class to strawberry.scalar() is deprecated. "
            "Use StrawberryConfig.scalar_map instead for better type checking support. "
            "See: https://strawberry.rocks/docs/types/scalars",
            DeprecationWarning,
            stacklevel=3,
        )
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
