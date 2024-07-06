import sys
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    NewType,
    Optional,
    TypeVar,
    Union,
    overload,
)

from strawberry.types.scalar import ScalarWrapper, _process_scalar

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
    authenticated: bool = False,
    inaccessible: bool = False,
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Optional[Iterable[str]] = (),
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
    authenticated: bool = False,
    inaccessible: bool = False,
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Optional[Iterable[str]] = (),
) -> _T: ...


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
    authenticated: bool = False,
    inaccessible: bool = False,
    policy: Optional[List[List[str]]] = None,
    requires_scopes: Optional[List[List[str]]] = None,
    tags: Optional[Iterable[str]] = (),
) -> Any:
    """Annotates a class or type as a GraphQL custom scalar.

    Args:
        cls: The class or type to annotate
        name: The GraphQL name of the scalar
        description: The description of the scalar
        specified_by_url: The URL of the specification
        serialize: The function to serialize the scalar
        parse_value: The function to parse the value
        parse_literal: The function to parse the literal
        directives: The directives to apply to the scalar
        authenticated: Whether to add the @authenticated directive
        inaccessible: Whether to add the @inaccessible directive
        policy: The list of policy names to add to the @policy directive
        requires_scopes: The list of scopes to add to the @requires directive
        tags: The list of tags to add to the @tag directive

    Returns:
        The decorated class or type

    Example usages:

    ```python
    strawberry.federation.scalar(
        datetime.date,
        serialize=lambda value: value.isoformat(),
        parse_value=datetime.parse_date,
    )

    Base64Encoded = strawberry.federation.scalar(
        NewType("Base64Encoded", bytes),
        serialize=base64.b64encode,
        parse_value=base64.b64decode,
    )


    @strawberry.federation.scalar(
        serialize=lambda value: ",".join(value.items),
        parse_value=lambda value: CustomList(value.split(",")),
    )
    class CustomList:
        def __init__(self, items):
            self.items = items
    ```
    """
    from strawberry.federation.schema_directives import (
        Authenticated,
        Inaccessible,
        Policy,
        RequiresScopes,
        Tag,
    )

    if parse_value is None:
        parse_value = cls

    directives = list(directives)

    if authenticated:
        directives.append(Authenticated())

    if inaccessible:
        directives.append(Inaccessible())

    if policy:
        directives.append(Policy(policies=policy))

    if requires_scopes:
        directives.append(RequiresScopes(scopes=requires_scopes))

    if tags:
        directives.extend(Tag(name=tag) for tag in tags)

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


__all__ = ["scalar"]
