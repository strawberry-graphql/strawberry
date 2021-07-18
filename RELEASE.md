Release type: minor

`strawberry.asgi.utils.get_graphiql_html`, `strawberry.flask.graphiql.render_graphiql_page`, `strawberry.sanic.graphiql.render_graphiql_page` are removed in favor of `strawberry.utils.graphiql.get_graphiql_html`.

`graphiql.html` template is now using latest version of `graphiql`. Added `SUBSCRIPTION_GRAPHQL_WS` template variable into `graphiql.html` that specifies whether it should use newer [graphql-ws](https://github.com/enisdenjo/graphql-ws) instead of unmaintained [subscriptions-transport-ws](https://github.com/apollographql/subscriptions-transport-ws). Implementations of new [protocol](https://github.com/enisdenjo/graphql-ws/blob/master/PROTOCOL.md) are yet to come.
