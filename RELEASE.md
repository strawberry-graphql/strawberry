---
release type: patch
social_messages:
  x: >-
    {project_name} {version} fixes `InputMutationExtension` — permission classes and other extensions on input-mutation fields now receive individual arguments instead of the wrapping input object.
  linkedin: >-
    {project_name} {version} fixes `InputMutationExtension`: permission classes and field extensions on input-mutation fields now receive the resolver's individual arguments (e.g. `name`, `color`) instead of the wrapping `input` object.
---

This release fixes `InputMutationExtension` to unpack its generated `input`
object into the resolver's individual keyword arguments before permission
classes and other field extensions run.

Previously, permission classes and field extensions on an input-mutation field
received the wrapping `input` object; they now receive the individual arguments
(for example `name` and `color`).

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
