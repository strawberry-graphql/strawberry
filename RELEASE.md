Release type: patch

This release fixes a number of problems with single-result-operations over
`graphql-transport-ws` protocol

- operation **IDs** now share the same namespace as streaming operations
  meaning that they cannot be reused while the others are in operation

- single-result-operations now run as *tasks* meaning that messages related
  to them can be overlapped with other messages on the websocket.

- single-result-operations can be cancelled with the `complete` message.
