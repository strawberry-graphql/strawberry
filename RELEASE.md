Release type: minor

A method on `strawberry.Schema` can now be overridden to validate connection attempts
for protocols `graphql_transport_ws` or `graphql_ws`.

```python
class Schema(strawberry.Schema):
    async def on_ws_connect(
        self, params: Dict[str, Any]
    ) -> Union[False, None, Dict[str, Any]]:
        user = await authenticate(params.get("authorization"), "")
        if not user:
            return False  # reject connection
        params["user"] = user  # for use by resolvers
        # return custom connection response payload to user
        return {"username": user.name, "karma": user.karma}
```

This offers similar functionality to other frameworks such as `onConnect` in Appollo Server.
