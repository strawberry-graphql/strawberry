Release type: minor

This release moves the `Connection` implementation outside the relay package,
allowing it to be used for general-purpose cursor pagination.

The following now can be imported from `strawberry.pagination`:

- `Connection` - base generic class for implementing connections
- `ListConnection` - a limit-offset implementation of the connection
- `connection` - field decorator for creating connections

Those can still be imported from the relay package for backwards compatibility,
but will emit a deprecation warning.

The schema config option `relay_max_results` has been renamed to
`connection_max_results`. The old name is still accepted but will emit a
deprecation warning.

A codemod is available to automatically update your imports and config:

```bash
strawberry upgrade update-relay-imports .
```

You can read more about connections in the
[Strawberry Connection Docs](https://strawberry.rocks/docs/guides/pagination/connections).
