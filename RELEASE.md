Release type: minor

This release moves the `Connection` implementation outside the relay package,
allowing it to be used for general-purpose cursor pagination.

The following now can be imported from `strawberry.pagination`:

- `Connection` - base generic class for implementing connections
- `ListConnection` - a limit-offset implementation of the connection
- `connection` - field decorator for creating connections

Those can still be used together with the relay package, but importing from it
is now deprecated.

You can read more about connections in the
[Strawberry Connection Docs](https://strawberry.rocks/docs/guides/pagination/connections).
