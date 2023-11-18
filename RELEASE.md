Release type: minor

Adds an optional `extensions` parameter to `strawberry.federation.field`, with default value `None`. The key is passed through to `strawberry.field`, so the functionality is exactly as described [here](https://strawberry.rocks/docs/guides/field-extensions).

Example:

```python
strawberry.federation.field(extensions=[InputMutationExtension()])
```
