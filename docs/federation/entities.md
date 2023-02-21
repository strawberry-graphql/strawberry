---
title: Entities (Apollo Federation)
---

# Entities (Apollo Federation)

In a federated graph, an
[entity](https://www.apollographql.com/docs/federation/entities) is an object
type that can resolve its fields across multiple subgraphs.

Entities have a unique identifier, called a key, that is used to fetch them from
a subgraph. In Strawberry entities are defined by annotating a type with the
`@strawberry.federation.type` decorator, like in example below:

```python
import strawberry


@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    title: str
```

You can also use the `Key` directive manually, like so:

```python
import strawberry

from strawberry.federation.schema_directives import Key


@strawberry.type(directives=[Key(fields="id")])
class Book:
    id: strawberry.ID
    title: str
```

# Resolving references

When a GraphQL operation references an entity across multiple services, the
Apollo Router will fetch the entity from the subgraph that defines it. To do
this, the subgraph needs to be able to resolve the entity by its key. This is
done by defining a class method called `resolve_reference` on the entity type.

For example, if we have a `Book` entity type, we can define a
`resolve_reference` method like this:

```python
import strawberry


@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    title: str

    @classmethod
    def resolve_reference(cls, id: strawberry.ID) -> "Book":
        # here we could fetch the book from the database
        # or even from an API
        return Book(id=id, title="My Book")
```

Strawberry provides a default implementation of `resolve_reference` that
instantiates the object type using the data coming from the key. This means that
you can omit the `resolve_reference` method if you don't need to fetch any
additional data for your object type, like in the example below:

```python
import strawberry


@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    reviews_count: int = strawberry.field(resolver=lambda: 3)
```

In the example above we are creating an entity called `Book` that has a `title`
field and a `reviews_count` field. This entity will contribute to the `Book`
entity in the supergraph and it will provide the `reviews_count` field.

When the Apollo Router fetches the `Book` entity from this subgraph, it will
call the `resolve_reference` method with the `id` of the book and, as mentioned
above, Strawberry will instantiate the `Book` type using the data coming from
the key.
