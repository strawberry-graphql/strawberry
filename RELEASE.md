Release type: patch

Fixes a concurrency bug where extension state could leak between
requests running in parallel.

Two cases were affected:

- Custom extensions that read `self.execution_context` (e.g. inside
  `get_results`) and were passed as instances to `extensions=[…]` —
  concurrent requests could observe each other's `ExecutionContext`.
- The built-in `ApolloTracingExtension`, `DatadogTracingExtension`,
  and `OpenTelemetryExtension` (plus their `*Sync` variants) — when
  passed as instances, concurrent requests' tracing data could be
  mixed.

Both are now isolated per request, so passing tracing extensions as
instances is safe.

If you write custom extensions, note that reading
`self.execution_context` outside an extension lifecycle hook
(`on_operation`, `on_validate`, `on_parse`, `on_execute`, `resolve`,
`get_results`) now raises `RuntimeError` instead of returning a stale
value.
