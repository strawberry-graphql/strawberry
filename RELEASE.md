Release type: minor

Enums can now be registered via `Annotated`. The preferred way is still using
`@strawberry.enum` as a decorator, but when you need to expose an existing enum
under a different name or alias, `Annotated` works as a proper type alias in all
type checkers:

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
