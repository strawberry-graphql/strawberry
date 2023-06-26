Release type: minor

This release adds support for declaring union types using `typing.Annotated`
instead of `strawberry.union(name, types=...)`.

Code using the old syntax will continue to work, but it will trigger a
deprecation warning. Using Annotated will improve type checking and IDE support
especially when using `pyright`.

Before:

```python
Animal = strawberry.union("Animal", (Cat, Dog))
```

After:

```python
from typing import Annotated, Union

Animal = Annotated[Union[Cat, Dog], strawberry.union("Animal")]
```
