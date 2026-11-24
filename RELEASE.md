---
release type: minor
---

This release adds support for combining permissions with the `|` operator.
Access is granted if any of the combined permissions grants it. Permissions are
checked from left to right, sync and async permissions can be mixed, and
chaining (`A() | B() | C()`) produces a single combined permission:

```python
import strawberry
from strawberry.permission import PermissionExtension


@strawberry.type
class User:
    @strawberry.field(
        extensions=[
            PermissionExtension(
                # require auth AND (user is the owner OR user is staff)
                permissions=[IsAuthenticated(), IsOwner() | IsStaff()]
            )
        ]
    )
    def ssn(self) -> str:
        return "555-55-5555"
```

When none of the combined permissions grants access, the error of the first
permission is raised. A combined permission adds a single schema directive named
after the sorted permission class names, for example `@isOwnerOrIsStaff`.
Subclass the new `OrPermission` class to give a combination its own name and
error.
