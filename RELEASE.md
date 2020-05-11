Release type: patch

Add support for setting `root_value` in asgi.

Usage:
```python
schema = strawberry.Schema(query=Query)
app = strawberry.asgi.GraphQL(schema, root_value=Query())
```
