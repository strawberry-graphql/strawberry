---
title: Multipart subscriptions
---

# Multipart subscriptions

Strawberry supports subscription over multipart responses. This is an
[alternative protocol](https://www.apollographql.com/docs/router/executing-operations/subscription-multipart-protocol/)
created by [Apollo](https://www.apollographql.com/) to support subscriptions
over HTTP, and it is supported by default by Apollo Client.

## Support

We support multipart subscriptions in the following HTTP libraries:

- Django (only in the Async view)
- ASGI
- Litestar
- FastAPI
- AioHTTP
- Quart

## Usage

Multipart subscriptions are opt-in. Enable them by including
`MULTIPART_SUBSCRIPTION_PROTOCOL` in your integration's
`subscription_protocols`:

```python
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import (
    GRAPHQL_TRANSPORT_WS_PROTOCOL,
    GRAPHQL_WS_PROTOCOL,
    MULTIPART_SUBSCRIPTION_PROTOCOL,
)

from api.schema import schema

graphql_router = GraphQLRouter(
    schema,
    subscription_protocols=[
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL,
        MULTIPART_SUBSCRIPTION_PROTOCOL,
    ],
)
```
