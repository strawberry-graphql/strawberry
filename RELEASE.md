Release type: minor

Remove deprecated `strawberry server` CLI command, deprecated since [0.283.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.283.0).

### Migration guide

**Before (deprecated):**
```bash
strawberry server myapp:schema
```

**After:**
```bash
strawberry dev myapp:schema
```
