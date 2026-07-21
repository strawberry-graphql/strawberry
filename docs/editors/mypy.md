---
title: Mypy
---

# Mypy

Strawberry works with [Mypy](https://mypy.readthedocs.io/en/stable/) out of the
box thanks to
[`dataclass_transform`](https://typing.readthedocs.io/en/latest/spec/dataclasses.html#dataclass-transform).
No plugin is needed for standard Strawberry types, inputs, interfaces, enums,
scalars, or unions.

## Pydantic integration

If you use `strawberry.experimental.pydantic`, add **both** the pydantic and
strawberry plugins to your mypy configuration:

```ini
[mypy]
plugins = pydantic.mypy, strawberry.ext.mypy_plugin
```

Or in `pyproject.toml`:

```toml
[tool.mypy]
plugins = ["pydantic.mypy", "strawberry.ext.mypy_plugin"]
```

The strawberry plugin synthesises `__init__`, `to_pydantic()` and
`from_pydantic()` on pydantic-decorated classes so that mypy can see them.

## Enums

The preferred way to register an enum is with the decorator:

```python
from enum import Enum
import strawberry


@strawberry.enum
class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
```

If you need to expose an existing enum under a different name or alias, use
`Annotated` instead of assigning `strawberry.enum(IceCreamFlavour)` to a
variable — mypy treats the latter as a value, not a type, so it cannot be used
in annotations.

```python
from typing import Annotated
import strawberry

MyIceCreamFlavour = Annotated[IceCreamFlavour, strawberry.enum(description="...")]
```

`MyIceCreamFlavour` is a proper type alias that mypy and Pyright accept in
annotations.
