---
release type: patch
---

`InputMutationExtension` now unpacks its generated `input` argument into the
resolver's individual keyword arguments during argument conversion, instead of
doing so in a field-extension resolver.

This is mostly an internal cleanup, but it has one observable effect: permission
classes and other field extensions applied to an input-mutation field now
receive the resolver's individual arguments (for example `name` and `color`)
instead of the wrapping `input` object.

```python
import strawberry
from strawberry.field_extensions import InputMutationExtension
from strawberry.permission import BasePermission


class IsAuthenticated(BasePermission):
    message = "Not authenticated"

    def has_permission(self, source, info, **kwargs) -> bool:
        # Previously: kwargs == {"input": CreateFruitInput(name=..., color=...)}
        # Now:        kwargs == {"name": ..., "color": ...}
        return True


@strawberry.type
class Mutation:
    @strawberry.mutation(
        extensions=[InputMutationExtension()],
        permission_classes=[IsAuthenticated],
    )
    def create_fruit(self, name: str, color: str) -> Fruit:
        return Fruit(name=name, color=color)
```
