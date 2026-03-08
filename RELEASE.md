Release type: minor

The strawberry mypy plugin has been restored with minimal support for
`strawberry.experimental.pydantic` types. If you use pydantic integration,
add the plugin to your mypy configuration:

```ini
[mypy]
plugins = pydantic.mypy, strawberry.ext.mypy_plugin
```

If you don't use pydantic types, no plugin is needed — `dataclass_transform`
handles everything else.

Additionally, enums can now be registered via `Annotated`, which works as a
proper type alias in all type checkers:

```python
from typing import Annotated
from enum import Enum
import strawberry


class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"


MyIceCreamFlavour = Annotated[
    IceCreamFlavour, strawberry.enum(description="Ice cream flavours")
]


@strawberry.type
class Query:
    @strawberry.field
    def flavour(self) -> MyIceCreamFlavour:
        return IceCreamFlavour.VANILLA
```
