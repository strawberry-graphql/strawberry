Release type: minor

Remove deprecated `_type_definition` and `_enum_definition` aliases, deprecated since [0.187.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.187.0).

### Migration guide

**Before (deprecated):**
```python
type_def = MyType._type_definition
enum_def = MyEnum._enum_definition
```

**After:**
```python
type_def = MyType.__strawberry_definition__
enum_def = MyEnum.__strawberry_definition__
```
