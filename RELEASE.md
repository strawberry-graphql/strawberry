Release type: minor

`Schema(extensions=...)` now accepts a class or a zero-arg factory and
builds a fresh extension per request. This fixes a race where shared
instances leaked `ExecutionContext` across concurrent requests, which
also produced mixed traces in `ApolloTracingExtension`,
`ApolloFederationTracingExtension`, `DatadogTracingExtension`, and
`OpenTelemetryExtension`.

```python
schema = strawberry.Schema(
    Query,
    extensions=[
        MaxTokensLimiter,
        lambda: MyExtension(arg=...),
    ],
)
```

Passing an instance is now deprecated. `extensions` no longer accepts
`SchemaExtension` instances in the type signature, so mypy and pyright
will flag existing call sites. Instances still work at runtime for
backwards compatibility, but the same object is reused for every
request, so concurrent requests can see each other's
`ExecutionContext`. Switch to the class or a factory for per-request
isolation and to silence the warning.
