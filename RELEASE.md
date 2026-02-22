Release type: minor

The strawberry mypy plugin has been removed. It is no longer needed thanks to
`@dataclass_transform`, overloaded signatures, and the `StrawberryTypeFromPydantic`
protocol.

If you still have `strawberry.ext.mypy_plugin` in your mypy configuration, it will
emit a `DeprecationWarning` and can be safely removed. Pydantic users only need
the `pydantic.mypy` plugin.
