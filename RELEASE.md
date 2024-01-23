Release type: patch

This release fixes a small issue in the GraphQL Transport websocket
where the connection would fail when receiving extra parameters
in the payload sent from the client.

This would happen when using Apollo Sandbox.
