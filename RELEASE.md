Release type: minor

In this release we removed the `--log-operations` option from the
`strawberry server` command. The option only worked for WebSocket connections to
the debug server, and had limited utility.

Removing this option allowed us to remove the undocumented `debug` option from
all HTTP view integrations and WebSocket protocol implementation, simplifying
the codebase.
