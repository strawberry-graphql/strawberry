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

# Limitations

At the moment, we don't support the following features:

- Changing the status code of the response
- Changing the headers of the response

We might add support for these features in the future, but it's clear how they
would work in the context of a subscription. If you have any ideas feel free to
reach out on our [discord server](https://strawberry.rocks/discord).
