Release type: minor

This release fixes a regression in the legacy GraphQL over WebSocket protocol.
Legacy protocol implementations should ignore client message parsing errors.
During a recent refactor, Strawberry changed this behavior to match the new protocol, where parsing errors must close the WebSocket connection.
The expected behavior is restored and adequately tested in this release.
