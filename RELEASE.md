Release type: minor

You can now configure your schemas to provide a custom subclass of
`strawberry.types.Info` to your types and queries.

```py
import strawberry
from strawberry.schema.config import StrawberryConfig

from .models import ProductModel


class CustomInfo(strawberry.Info):
    def is_selected(field: str) -> bool:
        """Check if the field is selected on the top-level of the query."""
        return field in [sel.name for sel in info.selected_fields]


@strawberry.type
class Product:
    id: strawberry.ID
    orders: list[Order]


@strawberry.type
class Query:
    @strawberry.field
    def product(self, id: strawberry.ID, info: CustomInfo) -> Product:
        kwargs = {"id": id}

        if info.is_selected("orders"):
            # Do some expensive operation here that we wouldn't want to
            # do if the field wasn't selected.
            kwargs["orders"] = ...

        return Product(**kwargs)


schema = strawberry.Schema(
    Query,
    config=StrawberryConfig(info_class=CustomInfo),
)
```
