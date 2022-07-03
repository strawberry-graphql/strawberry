Release type: patch

This release fixes a breaking internal error in mypy plugin for the following case.
- using positional arguments to pass a resolver for `strawberry.field()` or `strawberry.mutation()`

```python
failed: str = strawberry.field(resolver)
successed: str = strawberry.field(resolver=resolver)
```

now mypy returns an error with `"field()" or "mutation()" only takes keyword arguments` message
rather than an internal error.
