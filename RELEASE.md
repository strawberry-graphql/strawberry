Release type: minor

Rename `Extension` to `SchemaExtension` to pave the way for FieldExtensions.
Importing `Extension` from `strawberry.extensions` will now raise a deprecation
warning.

Before:

```python
from strawberry.extensions import Extension
```

After:

```python
from strawberry.extensions import SchemaExtension
```
