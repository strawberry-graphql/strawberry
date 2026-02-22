---
title: Mypy
---

# Mypy

Strawberry works with [Mypy](https://mypy.readthedocs.io/en/stable/) out of the
box thanks to
[`dataclass_transform`](https://typing.readthedocs.io/en/latest/spec/dataclasses.html#dataclass-transform).
No plugin is needed for standard Strawberry types, inputs, interfaces, enums,
scalars, or unions.

## Pydantic integration

If you use `strawberry.experimental.pydantic`, add the **pydantic** plugin to
your mypy configuration:

```ini
[mypy]
plugins = pydantic.mypy
```

Or in `pyproject.toml`:

```toml
[tool.mypy]
plugins = ["pydantic.mypy"]
```

No Strawberry-specific plugin is required.

## Deprecated plugin

If you still have `strawberry.ext.mypy_plugin` in your mypy configuration, it
will emit a `DeprecationWarning` at startup. You can safely remove it — it is a
no-op.
