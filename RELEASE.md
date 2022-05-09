Release type: patch

This release fixes resolvers using functions with generic type variables raising a `MissingTypesForGenericError` error.

For example a resolver factory like the below can now be used:

```python
import strawberry
from typing import Type, TypeVar

T = TypeVar("T")  # or TypeVar("T", bound=StrawberryType) etc


def resolver_factory(strawberry_type: Type[T]):
    def resolver(id: strawberry.ID) -> T:
        # some actual logic here
        return strawberry_type(...)

    return resolver
```
