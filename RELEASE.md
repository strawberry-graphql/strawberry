Release type: patch

Operations over `graphql-transport-ws` now create the Context and perform validation on
the worker `Task`, thus not blocking the websocket from accepting messages.
