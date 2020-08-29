---
title: Federation
---

# Federation

Strawberry supports [Apollo Federation][1] out of the box, that means that you
can create services using Strawberry and federate them via Apollo Gateway.

> _NOTE_: we don’t have a gateway server, you’d need to always use Apollo
> Federation for this.

## Federated schema example

Let’s look at an example. We’ll define define a books application with two
federated services.

- book: a service with all the books we have
- reviews: a service with book reviews.

### Books service

```python
@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    title: str


@strawberry.type
class Query:
    all_books: List[Book] = strawberry.field(resolver=get_all_books)
```

We defined two types, `Book` and `Query`, `Query` has only one field that allows
to fetch all the books.

Meanwhile `Book` used the `strawberry.federation.type` decorator, as opposed to
the normal `strawberry.type`, this new decorator extend the base one and allows
to define federation specific attributes to the type.

In this case we are telling federation that our key is the `id` field.

> Keys are types’ primary keys. They are used by the gateway to query types
> between multiple services.

### Reviews service

Let’s look at how our review service looks like, we want to define a type for a
review but also extend the book to have a list of review.

```python
@strawberry.type
class Review:
    body: str


@strawberry.federation.type(extend=True, keys=["id"])
class Book:
    id: strawberry.ID = strawberry.federation.field(external=True)
    reviews: List[Review] = strawberry.field(resolver=get_reviews)

    @classmethod
    def resolve_reference(cls, id: strawberry.ID):
        return Book(id)
```

Now things are looking more interesting, the `Review` type is a normal type that
holds the content of the review.

Meanwhile we are able to extend the `Book` type by using
`strawberry.federation.type` again and passing `extend=True` as a parameter.
This tells federation that we are extending an already existing type.

In addition to that we are also declaring two fields on `Book`, one is the `id`
which is marked as external with `strawberry.federation.field(external=True)`,
this tells federation that this field is not available in this service, but
comes from another service.

The other field is `reviews` which results in a list of `Reviews` for this book.

> TODO: explain resolver reference

[1]: https://www.apollographql.com/docs/apollo-server/federation/introduction/ "Apollo Federation Introduction"
