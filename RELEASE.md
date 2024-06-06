Release type: patch

Adds the ability to use the `&` and `|` operators on permissions to form boolean logic. For example, if you want
a field to be accessible with either the `IsAdmin` or `IsOwner` permission you
could define the field as follows:

```python
import strawberry
from strawberry.permission import PermissionExtension, BasePermission


@strawberry.type
class Query:
    @strawberry.field(
        extensions=[
            PermissionExtension(
                permissions=[(IsAdmin() | IsOwner())], fail_silently=True
            )
        ]
    )
    def name(self) -> str:
        return "ABC"
```
