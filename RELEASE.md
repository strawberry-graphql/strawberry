Release type: minor

Permissions can now be combined with the `|` operator to require the user pass _either_ of the `has_permission` checks:

```python
import strawberry
from strawberry.permission import PermissionExtension


@strawberry.type
class User:
    @strawberry.field(
        extensions=[
            PermissionExtension(
                # require auth AND (node is current user OR current user is staff)
                permissions=[IsAuthenticated(), IsExactUser() | IsStaff()]
            )
        ]
    )
    def ssn(self) -> str:
        return "555-55-5555"
```
