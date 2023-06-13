import sys
from typing import (
    Any,
    Callable,
    Iterable,
    NewType,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from strawberry.custom_scalar import _process_scalar

# in python 3.10+ NewType is a class
if sys.version_info >= (3, 10):
    _T = TypeVar("_T", bound=Union[type, NewType])
else:
    _T = TypeVar("_T", bound=type)


def identity(x: _T) -> _T:  # pragma: no cover
    return x


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
    inaccessible: bool = False,
    tags: Optional[Iterable[str]] = (),
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
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Optional[Iterable[str]] = (),
) -> _T:
    ...


def scalar(
    cls=None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    specified_by_url: Optional[str] = None,
    serialize: Callable = identity,
    parse_value: Optional[Callable] = None,
    parse_literal: Optional[Callable] = None,
    directives: Iterable[object] = (),
    inaccessible: bool = False,
    tags: Optional[Iterable[str]] = (),
) -> Any:
    """Annotates a class or type as a GraphQL custom scalar.

    Example usages:

    >>> strawberry.federation.scalar(
    >>>     datetime.date,
    >>>     serialize=lambda value: value.isoformat(),
    >>>     parse_value=datetime.parse_date
    >>> )

    >>> Base64Encoded = strawberry.federation.scalar(
    >>>     NewType("Base64Encoded", bytes),
    >>>     serialize=base64.b64encode,
    >>>     parse_value=base64.b64decode
    >>> )

    >>> @strawberry.federation.scalar(
    >>>     serialize=lambda value: ",".join(value.items),
    >>>     parse_value=lambda value: CustomList(value.split(","))
    >>> )
    >>> class CustomList:
    >>>     def __init__(self, items):
    >>>         self.items = items

    """
    from strawberry.federation.schema_directives import Inaccessible, Tag

    if parse_value is None:
        parse_value = cls

    directives = list(directives)

    if inaccessible:
        directives.append(Inaccessible())

    if tags:
        directives.extend(Tag(name=tag) for tag in tags)

    def wrap(cls: Type):
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
