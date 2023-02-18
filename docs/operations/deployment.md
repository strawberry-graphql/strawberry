---
title: Deployment
---

# Deployment

Before deploying your GraphQL app to production you should disable `GraphiQL` and `Introspection`.

## Why are they a problem?

1. They can reveal sensitive information (e.g. internal business logic)

2. They make it easier for malicious parties to reverse engineer your GraphQL API

[See more on this topic](https://www.apollographql.com/blog/graphql/security/why-you-should-disable-graphql-introspection-in-production/)

## How to disable them

### GraphiQL

GraphiQL is useful during testing and development but should be disabled in production by default.

It can be turned off by setting the `graphiql` option to `False`

See the Strawberry Options documentation for the integration you are using for more information on how to disable it:

- [AIOHTTP](../integrations/aiohttp.md#options)
- [ASGI](../integrations/asgi.md#options)
- [Django](../integrations/django.md#options)
- [FastAPI](../integrations/fastapi.md#options)
- [Flask](../integrations/flask.md#options)
- [Sanic](../integrations/sanic.md#options)
- [Chalice](../integrations/chalice.md#options)
- [Starlette](../integrations/starlette.md#options)

### Introspection

Introspection should primarily be used as a discovery and diagnostic tool for testing and development, and should be disabled in production by default.

You can disable introspection by [adding a validation rule extension](../extensions/add-validation-rules.md#more-examples).

## Other considerations

### Query depth

You may also want to limit the query depth of GraphQL operations, which can be done via an [extension](../extensions/query-depth-limiter.md)

# More resources

See the documentation for the integration you are using for more information on deployment:

- [AIOHTTP](https://docs.aiohttp.org/en/stable/deployment.html)
- [Django](https://docs.djangoproject.com/en/4.0/howto/deployment/)
- [FastAPI](https://fastapi.tiangolo.com/deployment/)
- [Flask](https://flask.palletsprojects.com/en/2.0.x/deploying/)
- [Sanic](https://sanic.dev/en/guide/deployment/configuration.html)
- [Chalice](https://aws.github.io/chalice/quickstart.html#deploying)

The docs for [ASGI](https://asgi.readthedocs.io/en/latest/index.html) and [Starlette](https://www.starlette.io/) do not provide an official deployment guide, but you may find the documentation for other frameworks that use ASGI servers useful (e.g. [FastAPI](https://fastapi.tiangolo.com/deployment/))
