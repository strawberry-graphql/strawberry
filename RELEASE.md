Release type: minor

You can now configure your schemas to provide a custom subclass of
`strawberry.types.Info` to your types and queries.

```py
import strawberry
from strawberry.schema.config import StrawberryConfig

from .models import ProductModel


class CustomInfo(strawberry.Info):
    @property
    def selected_group_id(self) -> int | None:
        """Get the ID of the group you're logged in as."""
        return self.context["request"].headers.get("Group-ID")


@strawberry.type
class Group:
    id: strawberry.ID
    name: str


@strawberry.type
class User:
    id: strawberry.ID
    name: str
    group: Group


@strawberry.type
class Query:
    @strawberry.field
    def user(self, id: strawberry.ID, info: CustomInfo) -> Product:
        kwargs = {"id": id, "name": ...}

        if info.selected_group_id is not None:
            # Get information about the group you're a part of, if
            # available.
            kwargs["group"] = ...

        return User(**kwargs)


schema = strawberry.Schema(
    Query,
    config=StrawberryConfig(info_class=CustomInfo),
)
```
