Release type: minor

Remove deprecated extension legacy hooks (`on_request_start`, `on_request_end`, `on_validation_start`, `on_validation_end`, `on_parsing_start`, `on_parsing_end`), deprecated since [0.159.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.159.0).

### Migration guide

**Before (deprecated):**
```python
class MyExtension(SchemaExtension):
    def on_request_start(self): ...

    def on_request_end(self): ...
```

**After:**
```python
class MyExtension(SchemaExtension):
    def on_operation(self):
        # on_request_start logic
        yield
        # on_request_end logic
```
