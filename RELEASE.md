Release type: minor

This release improves the `Info` type, by adding support for default TypeVars
and by exporting it from the main module. This makes it easier to use `Info` in
your own code, without having to import it from `strawberry.types.info`.

### New export

By exporting `Info` from the main module, now you can do the follwing:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def info(self, info: strawberry.Info) -> str:
        # do something with info
        return "hello"
```

### Default TypeVars

The `Info` type now has default TypeVars, so you can use it without having to
specify the type arguments, just like we did in the example above. Make sure to
use the latest version of Mypy or Pyright for this. It also means that you can
only pass one value to it if you only care about the context type:

```python
import strawberry

from .context import Context


@strawberry.type
class Query:
    @strawberry.field
    def info(self, info: strawberry.Info[Context]) -> str:
        return info.context.user_id
```
