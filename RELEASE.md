Release type: minor

Remove deprecated `ExecutionContext.errors` property, deprecated since [0.276.2](https://github.com/strawberry-graphql/strawberry/releases/tag/0.276.2).

### Migration guide

**Before (deprecated):**
```python
class MyExtension(SchemaExtension):
    def on_execute(self):
        yield
        errors = self.execution_context.errors
```

**After:**
```python
class MyExtension(SchemaExtension):
    def on_execute(self):
        yield
        errors = self.execution_context.pre_execution_errors
```
