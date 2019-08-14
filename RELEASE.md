Release type: minor

Added support for defining query directives, example:

```python
import strawberry
from strawberry.directives import DirectiveLocation

@strawberry.type
class Query:
    cake: str = "made_in_switzerland"

@strawberry.directive(
    locations=[DirectiveLocation.FIELD], description="Make string uppercase"
)
def uppercase(value: str, example: str):
    return value.upper()

schema = strawberry.Schema(query=Query, directives=[uppercase])
```
