---
title: Multipart subscriptions
---

# Multipart subscriptions

Strawberry supports subscription over multipart responses. This is an
[alternative protocol](https://www.apollographql.com/docs/router/executing-operations/subscription-multipart-protocol/)
created by [Apollo](https://www.apollographql.com/) to support subscriptions
over HTTP, and it is supported by default by Apollo Client.

# Support

We support multipart subscriptions out of the box in the following HTTP
libraries:

- Django (only in the Async view)
- ASGI
- Litestar
- FastAPI
- AioHTTP
- Quart

# Usage

Multipart subscriptions are automatically enabled when using Subscription, so no
additional configuration is required.
