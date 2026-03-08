Release type: patch

The strawberry mypy plugin has been restored with minimal support for
`strawberry.experimental.pydantic` types. If you use pydantic integration,
add the plugin to your mypy configuration:

```ini
[mypy]
plugins = pydantic.mypy, strawberry.ext.mypy_plugin
```
