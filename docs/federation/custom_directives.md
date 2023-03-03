---
title: Exposing directives on the supergraph (Apollo Federation)
---

# Exposing directives on the supergraph (Apollo Federation)

By default (most)
[schema directives are hidden from the supergraph schema](https://www.apollographql.com/docs/federation/federated-types/federated-directives/#composedirective).
If you need to expose a directive to the supergraph, you can use the `compose`
parameter on the `@strawberry.federation.schema_directives` decorator, here's an
example:

```python
import strawberry


@strawberry.federation.schema_directive(
    locations=[Location.OBJECT], name="cacheControl", compose=True
)
class CacheControl:
    max_age: int
```

This will create a `cacheControl` directive and it will also use
[`@composeDirective`](https://www.apollographql.com/docs/federation/federated-types/federated-directives/#composedirective)
on the schema to make sure it is included in the supergraph schema.
