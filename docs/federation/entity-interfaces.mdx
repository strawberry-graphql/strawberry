---
title: Entity interfaces (Apollo Federation)
---

# Extending interfaces

[Entity interfaces](https://www.apollographql.com/docs/federation/federated-types/interfaces)
are similar to [entities](./entities.md), but usually can't contribute new
fields to the supergraph (see below for how to use `@interfaceObject` to extend
interfaces).

Strawberry allows to define entity interfaces using the
`@strawberry.federation.interface` decorator, here's an example:

```python
import strawberry


@strawberry.federation.interface(keys=["id"])
class Media:
    id: strawberry.ID
```

This will generate the following GraphQL type:

```graphql
type Media @key(fields: "id") @interface {
  id: ID!
}
```

# Extending Entity interfaces (Apollo Federation)

In federation you can use `@interfaceObject` to extend interfaces from other
services. This is useful when you want to add fields to an interface that is
implemented by types in other services.

Entity interfaces that extend other interfaces are defined by annotating an
interface with the `@strawberry.federation.interface_object` decorator, like in
example below:

```python
import strawberry


@strawberry.federation.interface_object(keys=["id"])
class Media:
    id: strawberry.ID
    title: str
```

This will generate the following GraphQL type:

```graphql
type Media @key(fields: "id") @interfaceObject {
  id: ID!
  title: String!
}
```

`@strawberry.federation.interface_object` is necessary because if we were to
extend the `Media` interface using `@strawberry.federation.interface`, we'd need
to also define all the types implementing the interface, which will make the
schema hard to maintain (every updated to the interface and types implementing
it would need to be reflected in all subgraphs declaring it).

# Resolving references

Entity interfaces are also used to resolve references to entities. The same
rules as [entities](./entities.md) apply here. Here's a basic example:

```python
import strawberry


@strawberry.federation.interface_object(keys=["id"])
class Media:
    id: strawberry.ID
    title: str

    # TODO: check this

    @classmethod
    def resolve_reference(cls, id: strawberry.ID) -> "Media":
        # here we could fetch the media from the database
        # or even from an API
        return Media(id=id, title="My Media")
```
