Release type: minor

Remove deprecated `asserts_errors` parameter from test clients, deprecated since [0.246.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.246.0).

### Migration guide

**Before (deprecated):**
```python
result = client.query(query, asserts_errors=False)
```

**After:**
```python
result = client.query(query, assert_no_errors=False)
```
