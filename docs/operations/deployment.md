---
title: Deployment
---

# Deployment

Before deploying your GraphQL app to production you should disable `GraphiQL` and `Introspection`.

## Why are they a problem?
1. They can reveal sensitive information (e.g. internal business logic)

2. They make it easier for malicious actors to reverse engineer your GraphQL API

[See more on this topic](https://www.apollographql.com/blog/graphql/security/why-you-should-disable-graphql-introspection-in-production/)

## How to disable them

### GraphiQL
GraphiQL is useful during testing and development but should be disabled in production by default.

It can be turned off by setting the `graphiql` option to `False`

See the Strawberry Options documentation for the integration you are using for more information on how to disable it:
- [AIOHTTP](./integrations/aiohttp.md#options)
- [ASGI](./integrations/asgi.md#options)
- [Django](./integrations/django.md#options)
- [FastAPI](./integrations/fastapi.md#options)
- [Flask](./integrations/flask.md#options)
- [Sanic](./integrations/sanic.md#options)
- [Chalice](./integrations/chalice.md#options)
- [Starlette](./integrations/starlette.md#options)

### Introspection
Introspection should primarily be used as a discovery and diagnostic tool for testing and development, and should be disabled in production by default.

You can disable introspection by [adding a validation rule extension](../extensions/add-validation-rules.md#more-examples).
