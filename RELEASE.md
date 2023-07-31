Release type: minor

This release changes the way we override the type's `__annotations__`
when passing `graphql_type` to a field to preserve `Annotated` arguments
for future introspection.

For example:

```python
@strawberry.type
class Fruit:
    code: Annotated[str, "something"] = strawberry.field(graphql_type=int)


print(Fruit.__annotations__)
```

Before this would print: `{"code": int}`

Now this will print: `{"code": Annotated[int, "something"]}`

NOTE: This does not work for future references yet. Support for that will
come in a future release.
