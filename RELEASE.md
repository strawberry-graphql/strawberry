Release type: minor

Remove deprecated `debug-server` extra from `pyproject.toml`, deprecated since [0.283.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.283.0).

### Migration guide

**Before (deprecated):**
```bash
pip install strawberry-graphql[debug-server]
```

**After:**
```bash
pip install strawberry-graphql[cli]
```
