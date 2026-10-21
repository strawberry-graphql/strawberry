Release type: minor

Add a `subscription_url` option to the HTTP views to configure the websocket URL
used by GraphiQL for subscriptions.

When unset, the URL is derived from the page URL as before. This is useful when
subscriptions are served from a different URL than the main GraphQL endpoint, for
example when routed separately by a reverse proxy:

```python
from strawberry.asgi import GraphQL

app = GraphQL(schema, subscription_url="wss://example.com/ws/graphql")
```
