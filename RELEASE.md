Release type: minor

This release adds support for making Relay connection optional, this is useful
when you want to add permission classes to the connection and not fail the whole
query if the user doesn't have permission to access the connection.

Example:

```python
import strawberry
from strawberry import relay
from strawberry.permission import BasePermission


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    # This method can also be async!
    def has_permission(
        self, source: typing.Any, info: strawberry.Info, **kwargs
    ) -> bool:
        return False


@strawberry.type
class Fruit(relay.Node):
    code: relay.NodeID[int]
    name: str
    weight: float

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: strawberry.Info,
        node_ids: Iterable[str],
    ):
        return []


@strawberry.type
class Query:
    node: relay.Node = relay.node()

    @relay.connection(
        relay.ListConnection[Fruit] | None, permission_classes=[IsAuthenticated()]
    )
    def fruits(self) -> Iterable[Fruit]:
        # This can be a database query, a generator, an async generator, etc
        return all_fruits.values()
```
