Release type: minor

This releases updates the ASGI class to make it easier to override `get_http_response`.

`get_http_response` has been now removed from strawberry.asgi.http and been moved to be
a method on the ASGI class.

A new `get_graphiql_response` method has been added to make it easier to provide a different GraphiQL interface.
