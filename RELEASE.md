Release type: minor

Support "void" functions

It is now possible to have a resolver that returns "None". Strawberry will automatically assign the new `Void` scalar in the schema
and will always send `null` in the response

## Exampe

```python
@strawberry.type
class Mutation:
    @strawberry.field
    def do_something(self, arg: int) -> None:
        return
```
results in this schema:
```grapqhl
type Mutation {
    doSomething(arg: Int!): Void
}
```
