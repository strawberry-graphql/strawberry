---
title: Using silent permissions on optional fields
---

# Cannot use fail_silently on non-optional or non-list field

## Description

This error is thrown when a permission extension is configured to use silent
permissions on a field that is required and not a list:

```python
import strawberry
from strawberry.permission import PermissionExtension


@strawberry.type
class Query:
    @strawberry.field(
        extensions=[PermissionExtension([IsAuthorized()], fail_silently=True)]
    )
    def name(
        self,
    ) -> str:  # This is a required field, the schema type will be NonNull (String!)
        return "ABC"


schema = strawberry.Schema(query=Query)
```

This happens because fail_silently is suppsed to hide the field from a user
without an error in case of no permissions. However, non-nullable fields always
raise an error when they are set to null. The only exception to that is a list,
because an empty list can be returned.

## How to fix this error

You can fix this error by making this field an optional field. For example, the
following code will fix this error in the above example:

```python
import strawberry
from strawberry.permission import PermissionExtension


@strawberry.type
class Query:
    @strawberry.field(
        extensions=[PermissionExtension([IsAuthorized()], fail_silently=True)]
    )
    def name(self) -> str | None:  # This is now a nullable field
        return "ABC"


schema = strawberry.Schema(query=Query)
```

Alternatively, not using `fail_silently` might be a good design choice as well.
