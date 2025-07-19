Release type: patch

This release fixes the resolution of `Generics` when specializing using a union
defined with `Annotated`, like in the example below:

```python
from typing import Annotated, Generic, TypeVar, Union
import strawberry

T = TypeVar("T")


@strawberry.type
class User:
    name: str
    age: int


@strawberry.type
class ProUser:
    name: str
    age: float


@strawberry.type
class GenType(Generic[T]):
    data: T


GeneralUser = Annotated[Union[User, ProUser], strawberry.union("GeneralUser")]


@strawberry.type
class Response(GenType[GeneralUser]): ...


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> Response: ...


schema = strawberry.Schema(query=Query)
```

Before this would raise a `TypeError`, now it works as expected.
