Release type: patch

Fixed field resolvers with nested generic return types
(e.g. `list`, `Optional`, `Union` etc) raising TypeErrors.
This means resolver factory methods can now be correctly type hinted.

For example the below would previously error unless you ommited all the
type hints on `resolver_factory` and `actual_resolver` functions.
```python
from typing import Callable, Optional, Type, TypeVar

import strawberry


@strawberry.type
class Cat:
    name: str


T = TypeVar("T")


def resolver_factory(type_: Type[T]) -> Callable[[], Optional[T]]:
    def actual_resolver() -> Optional[T]:
        # load rows from database and cast to type etc
        ...

    return actual_resolver


@strawberry.type
class Query:
    cat: Cat = strawberry.field(resolver_factory(Cat))


schema = strawberry.Schema(query=Query)
```