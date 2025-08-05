---
title: Field extensions
---

# Field extensions

Field extensions are a great way to implement reusable logic such as permissions
or pagination outside your resolvers. They wrap the underlying resolver and are
able to modify the field and all arguments passed to the resolver.

<Note>

The following examples only cover sync execution. To use extensions in async
contexts, please have a look at
[Async Extensions and Resolvers](#async-extensions-and-resolvers)

</Note>

```python
import strawberry
from strawberry.extensions import FieldExtension


class UpperCaseExtension(FieldExtension):
    def resolve(
        self, next_: Callable[..., Any], source: Any, info: strawberry.Info, **kwargs
    ):
        result = next_(source, info, **kwargs)
        return str(result).upper()


@strawberry.type
class Query:
    @strawberry.field(extensions=[UpperCaseExtension()])
    def string(self) -> str:
        return "This is a test!!"
```

In this example, the `UpperCaseExtension` wraps the resolver of the `string`
field (`next`) and modifies the resulting string to be uppercase. The extension
will be called instead of the resolver and receives the resolver function as the
`next` argument. Therefore, it is important to not modify any arguments that are
passed to `next` in an incompatible way.

<CodeGrid>

```graphql
query {
  string
}
```

```json
{
  "string": "THIS IS A TEST!!"
}
```

</CodeGrid>

## Modifying the field

<Warning>

Most of the `StrawberryField` API is not stable and might change in the future
without warning. Stable features include: `StrawberryField.type`,
`StrawberryField.python_name`, and `StrawberryField.arguments`.

</Warning>

In some cases, the extended field needs to be compatible with the added
extension. `FieldExtension` provides an `apply(field: StrawberryField)` method
that can be overriden to modify the field. It is called during _Schema
Conversion_. In the following example, we use `apply` to add a directive to the
field:

```python
import time
import strawberry
from strawberry.extensions import FieldExtension
from strawberry.schema_directive import Location
from strawberry.types.field import StrawberryField


@strawberry.schema_directive(locations=[Location.FIELD_DEFINITION])
class Cached:
    time: int = 100


class CachingExtension(FieldExtension):
    def __init__(self, caching_time=100):
        self.caching_time = caching_time
        self.last_cached = 0.0
        self.cached_result = None

    def apply(self, field: StrawberryField) -> None:
        field.directives.append(Cached(time=self.caching_time))

    def resolve(
        self, next_: Callable[..., Any], source: Any, info: strawberry.Info, **kwargs
    ) -> Any:
        current_time = time.time()
        if self.last_cached + self.caching_time > current_time:
            return self.cached_result
        self.cached_result = next_(source, info, **kwargs)
        return self.cached_result
```

<CodeGrid>

```python
@strawberry.type
class Client:

    @strawberry.field(extensions=[CachingExtensions(caching_time=200)])
    def analyzed_hours(self, info) -> int:
        return do_expensive_computation()
```

```graphql
type Client {
    analyzedHours: Int! @Cached(time=200)
}
```

</CodeGrid>

## Combining multiple field extensions

When chaining multiple field extensions, the last extension in the list is
called first. Then, it calls the next extension until it reaches the resolver.
The return value of each extension is passed as an argument to the next
extension. This allows for creating a chain of field extensions that each
perform a specific transformation on the data being passed through them.

```python
@strawberry.field(extensions=[LowerCaseExtension(), UpperCaseExtension()])
def my_field():
    return "My Result"
```

<Tip>

**Order matters**: the last extension in the list will be executed first, while
the first extension in the list extension will be applied to the field first.
This enables cases like adding relay pagination in front of an extension that
modifies the field's type.

</Tip>

## Async Extensions and Resolvers

Field Extensions support async execution using the `resolve_async` method. A
field extension can either support `sync`, `async`, or both. The appropriate
resolve function will be automatically chosen based on the type of resolver and
other extensions.

Since sync-only extensions cannot await the result of an async resolver, they
are not compatible with async resolvers or extensions.

The other way around is possible: you can add an async-only extension to a sync
resolver, or wrap sync-only extensions with it. This is enabled by an automatic
use of the `SyncToAsyncExtension`. Note that after adding an async-only
extension, you cannot wrap it with a sync-only extension anymore.

<Tip>

To optimize the performance of your resolvers, it's recommended that you
implement both the `resolve` and `resolve_async` methods when using an extension
on both sync and async fields. While the `SyncToAsyncExtension` is convenient,
it may add unnecessary overhead to your sync resolvers, leading to slightly
decreased performance.

</Tip>

```python
import strawberry
from strawberry.extensions import FieldExtension


class UpperCaseExtension(FieldExtension):
    def resolve(
        self, next: Callable[..., Any], source: Any, info: strawberry.Info, **kwargs
    ):
        result = next(source, info, **kwargs)
        return str(result).upper()

    async def resolve_async(
        self,
        next: Callable[..., Awaitable[Any]],
        source: Any,
        info: strawberry.Info,
        **kwargs
    ):
        result = await next(source, info, **kwargs)
        return str(result).upper()


@strawberry.type
class Query:
    @strawberry.field(extensions=[UpperCaseExtension()])
    async def string(self) -> str:
        return "This is a test!!"
```
