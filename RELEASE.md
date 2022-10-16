Release type: patch

This release fixes an issue that prevented using strawberry.lazy with relative paths.

The following should work now:

```python
@strawberry.type
class TypeA:
    b: Annotated["TypeB", strawberry.lazy(".type_b")]
```
