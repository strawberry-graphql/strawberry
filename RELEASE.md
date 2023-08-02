Release type: patch

This release fixes an issue in the `graphql-ws` implementation
where sending a `null` payload would cause the connection
to be closed.
