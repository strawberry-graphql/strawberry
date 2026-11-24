---
release type: minor
---

This release adds `strawberry.Context`, which lets a resolver receive the
request context as a parameter instead of reading `info.context`.

```python
@strawberry.type
class Query:
    @strawberry.field
    def user_id(self, context: strawberry.Context[MyContext]) -> str:
        return context.user_id
```

Type checkers see the parameter as `MyContext`, so it is typed without the mypy
plugin. It works in field, subscription and directive resolvers, and alongside
`Info` and other arguments.
