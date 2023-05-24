Release type: minor

A method on `strawberry.Schema` can now be overridden to validate connection attempts
for protocols `graphql_transport_ws` or `graphql_ws`.

```python
class MyView(GraphQLView):
    async def on_ws_connect(self, params: WSConnectionParams) -> None:
        user = await authenticate(params.request_params.get("authorization"), "")
        if not user:
            await params.reject()  # reject connection
        params.request_params["user"] = user  # for use by resolvers
        # return custom connection response payload to user
        params.response_params = {"username": user.name, "karma": user.karma}
```

This offers similar functionality to other frameworks such as `onConnect` in Appollo Server.
