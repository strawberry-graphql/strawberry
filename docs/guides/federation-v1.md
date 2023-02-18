---
title: Federation V1
---

<Warning>

This guide refers to Apollo Federation 1, if you're looking for the 2.0 guide,
please see the [federation v2](federation.md) guide.

You can also see the
[What's new in federation 2](https://www.apollographql.com/docs/federation/federation-2/new-in-federation-2/)
for more details.

</Warning>

# Apollo Federation V1 Guide

Apollo Federation allows you to combine multiple GraphQL APIs into one. This can
be extremely useful when working with a service oriented architecture.

Strawberry supports
[Apollo Federation](https://www.apollographql.com/docs/federation) out of the
box, that means that you can create services using Strawberry and federate them
via Apollo Gateway.

<Note>

We don’t have a gateway server, you’ll still need to use the Apollo Gateway for
this.

</Note>

## Federated schema example

Let’s look at an example on how to implement Apollo Federation using Strawberry.
Let's assume we have an application with two services that each expose a GraphQL
API:

1. `books`: a service to manage all the books we have
2. `reviews`: a service to manage book reviews

### Books service

Our `book` service might look something like this:

```python
@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    title: str


def get_all_books() -> List[Book]:
    return [Book(id=1, title="The Dark Tower")]


@strawberry.type
class Query:
    all_books: List[Book] = strawberry.field(resolver=get_all_books)


schema = strawberry.federation.Schema(query=Query)
```

We defined two types: `Book` and `Query`, where `Query` has only one field that
allows us to fetch all the books.

Notice that the `Book` type is using the `strawberry.federation.type` decorator,
as opposed to the normal `strawberry.type`, this new decorator extends the base
one and allows us to define federation-specific attributes on the type.

Here, we are telling the federation system that the `Book`'s `id` field is its
uniquely-identifying key.

<Note>

Federation keys can be thought of as primary keys. They are used by the gateway
to query types between multiple services and then join them into the augmented
type.

</Note>

### Reviews service

Now, let’s take a look at our review service: we want to define a type for a
review but also extend the `Book` type to have a list of reviews.

```python
@strawberry.type
class Review:
    id: int
    body: str


def get_reviews(root: "Book") -> List[Review]:
    return [
        Review(id=id_, body=f"A review for {root.id}")
        for id_ in range(root.reviews_count)
    ]


@strawberry.federation.type(extend=True, keys=["id"])
class Book:
    id: strawberry.ID = strawberry.federation.field(external=True)
    reviews_count: int
    reviews: List[Review] = strawberry.field(resolver=get_reviews)

    @classmethod
    def resolve_reference(cls, id: strawberry.ID):
        # here we could fetch the book from the database
        # or even from an API
        return Book(id=id, reviews_count=3)
```

Now things are looking more interesting; the `Review` type is a GraphQL type
that holds the contents of the review.

We've also been able to extend the `Book` type by using again
`strawberry.federation.type`, this time passing `extend=True` as an argument.
This is important because we need to tell federation that we are extending a
type that already exists, not creating a new one.

We have also declared three fields on `Book`, one of which is `id` which is
marked as `external` with `strawberry.federation.field(external=True)`. This
tells federation that this field is not available in this service, and that it
comes from another service.

The other fields are `reviews` (the list of `Reviews` for this book) and
`reviews_count` (the number of reviews for this book).

Finally, we also have a class method, `resolve_reference`, that allows us to
instantiate types when they are referred to by other services. The
`resolve_reference` method is called when a GraphQL operation references an
entity across multiple services. For example, when making this query:

```graphql
{
  # query defined in the books service
  books {
    title
    # field defined in the reviews service
    reviews {
      body
    }
  }
}
```

`resolve_reference` is called with the `id` of the book for each book returned
by the books service. Recall that above we defined the `id` field as the `key`
for the `Book` type. In this example we are creating an instance of `Book` with
the requested `id` and a fixed number of reviews.

If we were to add more fields to `Book` that were stored in a database, this
would be where we could perform queries for these fields' values.

Now we need to do is to define a `Query` type, even if our service only has one
type that is not used directly in any GraphQL query. This is because the GraphQL
spec mandates that a GraphQL server defines a Query type, even if it ends up
being empty/unused. Finally we also need to let Strawberry know about our Book
and Review types. Since they are not reachable from the `Query` field itself,
Strawberry won't be able to find them by default.

```python
@strawberry.type
class Query:
    _hi: str = strawberry.field(resolver=lambda: "Hello world!")


schema = strawberry.federation.Schema(query=Query, types=[Book, Review])
```

## The gateway

Now we have our services up and running, we need to configure a gateway to
consume our services. Apollo Gateway is the official gateway server for Apollo
Federation. Here's an example on how to configure the gateway:

```js
const { ApolloServer } = require("apollo-server");
const { ApolloGateway } = require("@apollo/gateway");

const gateway = new ApolloGateway({
  serviceList: [
    { name: "books", url: "http://localhost:8000" },
    { name: "reviews", url: "http://localhost:8080" },
  ],
});

const server = new ApolloServer({ gateway });

server.listen().then(({ url }) => {
  console.log(`🚀 Server ready at ${url}`);
});
```

When running this example you'll be able to run query like the following:

```graphql
{
  allBooks {
    id
    reviewsCount
    reviews {
      body
    }
  }
}
```

We have provided a full example that you can run and tweak to play with
Strawberry and Federation. The repo is available here:
[https://github.com/strawberry-graphql/federation-demo](https://github.com/strawberry-graphql/federation-demo)
