Release type: patch

This release fixes an issue with type duplication of generics.

You can now use a lazy type with a generic even if
the original type was already used with that generic in the schema.

Example:

```python3
@strawberry.type
class Query:
    regular: Edge[User]
    lazy: Edge[Annotated["User", strawberry.lazy(".user")]]
```
