---
title: Apollo Federation
---

# Apollo Federation

Strawberry supports
[Apollo Federation](https://www.apollographql.com/docs/federation/) out of the
box, that means that you can create services using Strawberry and federate them
via Apollo Gateway or Apollo Router.

Strawberry is a schema first library, to use Apollo Federation you need to add
directives to your schema, types and fields. Strawberry has built support for
directives, but it also provide shortcuts for Apollo Federation.

All shortcuts live under the `strawberry.federation` module. For example if you
want to create an
[Entity](https://www.apollographql.com/docs/federation/entities) you can do:

```python
@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    title: str
```

And strawberry will automatically add the right directives to the type and
schema.

# Getting started

If you want to get started with Apollo Federation, you can use our
[Apollo Federation guide](../guides/federation.md).
