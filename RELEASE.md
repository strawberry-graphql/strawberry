Release type: minor

This release add full support for async directives and fixes
and issue when using directives and async extensions.


```python
@strawberry.type
class Person:
    name: str = "Jess"

@strawberry.type
class Query:
    @strawberry.field
    def person(self) -> Person:
        return Person()

@strawberry.directive(
    locations=[DirectiveLocation.FIELD], description="Make string uppercase"
)
async def uppercase(value: str):
    return value.upper()

schema = strawberry.Schema(query=Query, directives=[uppercase])
```
