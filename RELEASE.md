Release type: minor

This release adds a new `on_ws_connect` method to all HTTP view integrations.
The method is called when a `graphql-transport-ws` or `graphql-ws` connection is
established and can be used to customize the connection acknowledgment behavior.

This is particularly useful for authentication, authorization, and sending a
custom acknowledgment payload to clients when a connection is accepted. For
example:

```python
class MyGraphQLView(GraphQLView):
    async def on_ws_connect(self, context: Dict[str, object]):
        connection_params = context["connection_params"]

        if not isinstance(connection_params, dict):
            # Reject without a custom graphql-ws error payload
            raise ConnectionRejectionError()

        if connection_params.get("password") != "secret:
            # Reject with a custom graphql-ws error payload
            raise ConnectionRejectionError({"reason": "Invalid password"})

        if username := connection_params.get("username"):
            # Accept with a custom acknowledgement payload
            return {"message": f"Hello, {username}!"}

        # Accept without a acknowledgement payload
        return await super().on_ws_connect(context)
```

Take a look at our documentation to learn more.
