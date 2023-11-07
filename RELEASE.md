Release type: minor

This release adds support for operation directives on operations, for
example the following is now working properly:

```graphql
query @debug {
    something
}
```

```python
from typing import Any

import strawberry
from strawberry.directive import DirectiveLocation


@strawberry.type
class Query:
    @strawberry.field
    def person(self) -> str:
        return "Bryce"


@strawberry.directive(locations=[DirectiveLocation.QUERY])
def debug(value: Any) -> Any:
    print("Value:", value)
    return value


schema = strawberry.Schema(query=Query, directives=[debug])
```
