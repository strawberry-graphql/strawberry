Release type: minor

This releases allows to use resolver without having 
to specify root and info arguments:

```python
def function_resolver() -> str:
    return "I'm a function resolver"

def function_resolver_with_params(x: str) -> str:
    return f"I'm {x}"

@strawberry.type
class Query:
    hello: str = strawberry.field(resolver=function_resolver)
    hello_with_params: str = strawberry.field(
        resolver=function_resolver_with_params
    )


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "I'm a function resolver"

    @strawberry.field
    def hello_with_params(self, x: str) -> str:
        return f"I'm {x}"
```

This makes it easier to reuse existing functions and makes code
cleaner when not using info or root.
