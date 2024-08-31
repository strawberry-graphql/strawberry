Release type: minor

This release adds support for multipart subscriptions in almost all[^1] of our
http integrations!

[Multipart subcriptions](https://www.apollographql.com/docs/router/executing-operations/subscription-multipart-protocol/)
are a new protocol from Apollo GraphQL, built on the
[Incremental Delivery over HTTP spec](https://github.com/graphql/graphql-over-http/blob/main/rfcs/IncrementalDelivery.md),
which is also used for `@defer` and `@stream`.

The main advantage of this protocol is that when using the Apollo Client
libraries you don't need to install any additional dependency, but in future
this feature should make it easier for us to implement `@defer` and `@stream`

Also, this means that you don't need to use Django Channels for subscription,
since this protocol is based on HTTP we don't need to use websockets.

[^1]: Flask, Chalice and the sync Django integration don't support this.
