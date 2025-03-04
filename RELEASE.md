Release type: minor

This release adds support for exporting schema created by a callable:

```bash
strawberry export-schema package.module:create_schema
```

when

```python
def create_schema():
    return strawberry.Schema(query=Query)
```
