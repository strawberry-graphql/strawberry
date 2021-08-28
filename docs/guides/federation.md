---
title: Federation
---

# Apollo Federation Guide

Strawberry supports [Apollo Federation][1] out of the box, that means that you
can create services using Strawberry and federate them via Apollo Gateway.

> _NOTE_: we don’t have a gateway server, you’d need to always use the Apollo
> Gateway for this.

Apollo Federation allows to combine multiple GraphQL APIs into one. This can be
extremely useful when working with micro-services.

## Federated schema example

Let’s look at an example on how to implement Apollo Federation using Strawberry,
We’ll have an application with two federated services.

1. book: a service with all the books we have
2. reviews: a service with book reviews.

### Books service

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

We defined two types, `Book` and `Query`, `Query` has only one field that allows
to fetch all the books.

Meanwhile `Book` used the `strawberry.federation.type` decorator, as opposed to
the normal `strawberry.type`, this new decorator extend the base one and allows
to define federation specific attributes to the type.

In this case we are telling federation that the key to uniquely identify a book is the `id` field.

> Federation keys can be thought primary keys. They are used by the gateway to query types
> between multiple services and then joining them into the augmented type.

### Reviews service

Let’s look at how our review service looks like, we want to define a type for a
review but also extend the book to have a list of review.

```python
@strawberry.type
class Review:
    body: str

def get_reviews() -> List[Review]:
    return [Review(body="This is a review")]

@strawberry.federation.type(extend=True, keys=["id"])
class Book:
    id: strawberry.ID = strawberry.federation.field(external=True)
    reviews: List[Review] = strawberry.field(resolver=get_reviews)

    @classmethod
    def resolve_reference(cls, id: strawberry.ID):
        return Book(id)
```

Now things are looking more interesting, the `Review` type is a GraphQL type
that holds the content of the review.

Meanwhile we are able to extend the `Book` type by using
`strawberry.federation.type` again and passing `extend=True` as a parameter.
This tells federation that we are extending an already existing type.

We are also declaring two fields on `Book`, one is the `id` which is marked as
external with `strawberry.federation.field(external=True)`, this tells
federation that this field is not available in this service, and **that** it
comes from another service.

The other field is `reviews` which results in a list of `Reviews` for this book.

Finally we also have a class method called `resolve_reference` that allows us to
resolve references to types. The `resolve_reference` method is called when a
GraphQL operation references an entities across multiple services. For example
when doing this query:

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

The `resolve_reference` method is called with the `id` of the book for each book
returned by the books service. This allows to our review service to fetch data
for the book. In our case we only need the book id so we instantiate a `Book`
object with the id and return it.

The last thing we need to do is to define a `Query` type, even if our service
only has one type that is not used directly in any GraphQL query. This is
because any GraphQL server requires the Query type to be defined.

In addition to that we also need to let Strawberry know about our Book and
Review types. Since they are not being used anywhere, Strawberry won't be able
to find them by default.

```python
@strawberry.type
class Query:
    _service: Optional[str]

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

[1]: https://www.apollographql.com/docs/federation "Apollo Federation Introduction"
