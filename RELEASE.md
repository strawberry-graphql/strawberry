Release type: minor

Adding the possiblity to process `payload` sent with a websockets `connection_init` message,
and provide a response payload included with the `connection_ack` message.  This can be useful for
customized authentication and to provide general information to the client.

## Example

Here is how one might subclass the Router to provide a custom handler class.  This example
uses the `GraphQLWSHandler`, but the `GraphQLTransportWSHandler` case is identical.

```python
from strawberry.fastapi import GraphQLRouter
from strawberry.fastapi.handlers import GraphQLTransportWSHandler, GraphQLWSHandler
class MyGraphQLWSHandler(GraphQLWSHandler):
    async def process_connection_payload(self, payload):
        if payload.get("name") == "bob":
            await self.close(4400, "Bob is banned")
            return
        return {"hello": "Welcome to our server!"}

class MyRouter(GraphQLRouter):
    graphql_ws_handler_class = MyGraphQLWSHandler

graphql_app = MyRouter(schema)
```
