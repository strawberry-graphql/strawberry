Release type: patch

Fix compatibility with Starlette 1.0.0 in the dev server by replacing
removed `add_route`/`add_websocket_route` methods with `Route`/`WebSocketRoute`
objects passed to the `Starlette` constructor.
