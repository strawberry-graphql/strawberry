---
release type: minor
---

This release fixes cross-site WebSocket hijacking (GHSA-873f-848v-759p).

Browsers don't apply CORS to WebSocket handshakes, so a page on another origin
could open a WebSocket to a Strawberry GraphQL endpoint with the user's cookies
attached. Applications that authenticate WebSockets from cookies could have
queries, mutations and subscriptions run as their users by another website.

Strawberry now checks the `Origin` header before accepting a WebSocket and
refuses handshakes from other origins with an HTTP 403 response. Same-origin
pages and clients that don't send an `Origin` header, such as mobile apps and
server-side clients, are not affected.

If your frontend is served from a different origin than your GraphQL endpoint,
list it in the new `allowed_origins` option:

```python
graphql_app = GraphQLRouter(schema, allowed_origins=["https://app.example.com"])
```

See the [breaking changes notes](https://strawberry.rocks/docs/breaking-changes/0.339.0)
for details.
