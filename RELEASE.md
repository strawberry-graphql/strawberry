Release type: patch

Fixed edge case where `Union` types raised an `UnallowedReturnTypeForUnion`
error when returning the correct type from the resolver. This also improves
performance of StrawberryUnion's `_resolve_union_type` from `O(n)` to `O(1)` in
the majority of cases where `n` is the number of types in the schema.

For
[example the below](https://play.strawberry.rocks/?gist=f7d88898d127e65b12140fdd763f9ef2))
would previously raise the error when querying `two` as `StrawberryUnion` would
incorrectly determine that the resolver returns `Container[TypeOne]`.

```python
import strawberry
from typing import TypeVar, Generic, Union, List, Type

T = TypeVar("T")

@strawberry.type
class Container(Generic[T]):
    items: List[T]

@strawberry.type
class TypeOne:
    attr: str

@strawberry.type
class TypeTwo:
    attr: str

def resolver_one():
    return Container(items=[TypeOne("one")])

def resolver_two():
    return Container(items=[TypeTwo("two")])

@strawberry.type
class Query:
    one: Union[Container[TypeOne], TypeOne] = strawberry.field(resolver_one)
    two: Union[Container[TypeTwo], TypeTwo] = strawberry.field(resolver_two)

schema = strawberry.Schema(query=Query)
```
