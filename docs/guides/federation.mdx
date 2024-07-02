---
title: Federation 2
---

# Apollo Federation 2 Guide

<Note>

This guide refers to Apollo Federation 2, if you're looking for the 1.0 guide,
please see the [federation v1](federation-v1.md) guide.

</Note>

Apollo Federation allows you to combine multiple GraphQL APIs into one. This can
be extremely useful when working with a service oriented architecture.

Strawberry supports
[Apollo Federation 2](https://www.apollographql.com/docs/federation/federation-2/new-in-federation-2/)
out of the box, that means that you can create services using Strawberry and
federate them via Apollo Gateway or Apollo Router.

## Federated schema example

Let’s look at an example on how to implement Apollo Federation using Strawberry.
Let's assume we have an application with two services that each expose a GraphQL
API:

1. `books`: a service to manage all the books we have
2. `reviews`: a service to manage book reviews

Our folder structure will look something like this:

```text
my-app/
├─ books/
│  ├─ app.py
├─ reviews/
│  ├─ app.py
```

<Note>

This guide assumes you've installed strawberry in both the books and reviews
service

</Note>

### Books service

Let's create the `books` service, copy the following inside `books/app.py`

```python
from typing import List

import strawberry


@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    title: str


def get_all_books() -> List[Book]:
    return [Book(id=strawberry.ID("1"), title="The Dark Tower")]


@strawberry.type
class Query:
    all_books: List[Book] = strawberry.field(resolver=get_all_books)


schema = strawberry.federation.Schema(query=Query, enable_federation_2=True)
```

<Note>

`enable_federation_2=True` is used to enable Apollo Federation 2 and currently
defaults to `False`. This will change in a future version of Strawberry.

</Note>

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

Copy the following inside `reviews/app.py`:

```python
from typing import List

import strawberry


@strawberry.type
class Review:
    id: int
    body: str


def get_reviews(root: "Book") -> List[Review]:
    return [
        Review(id=id_, body=f"A review for {root.id}")
        for id_ in range(root.reviews_count)
    ]


@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    reviews_count: int
    reviews: List[Review] = strawberry.field(resolver=get_reviews)

    @classmethod
    def resolve_reference(cls, id: strawberry.ID):
        # here we could fetch the book from the database
        # or even from an API
        return Book(id=id, reviews_count=3)


@strawberry.type
class Query:
    _hi: str = strawberry.field(resolver=lambda: "Hello World!")


schema = strawberry.federation.Schema(
    query=Query, types=[Book, Review], enable_federation_2=True
)
```

Now things are looking more interesting; the `Review` type is a GraphQL type
that holds the contents of the review.

But we also have a `Book` which has 3 fields, `id`, `reviews_count` and
`reviews`.

<Note>

In Apollo Federation 1 we'd need to mark the `Book` type as an extension and
also we'd need to mark `id` as an external field, this is not the case in Apollo
Federation 2.

</Note>

Finally, we also have a class method, `resolve_reference`, that allows us to
instantiate types when they are referred to by other services. The
`resolve_reference` method is called when a GraphQL operation references an
entity across multiple services. For example, when making this query:

```graphql
{
  # query defined in the books service
  allBooks {
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

We also defined a `Query` type that has a single field, `_hi`, which returns a
string. This is required because the GraphQL spec mandates that a GraphQL server
defines a Query type, even if it ends up being empty/unused.

Finally we also need to let Strawberry know about our Book and Review types.
Since they are not reachable from the `Query` field itself, Strawberry won't be
able to find them.

<Note>

If you don't need any custom logic for your resolve_reference, you can omit it
and Strawberry will automatically instanciate the type for you. For example, if
we had a `Book` type with only an `id` field, Strawberry would be able to
instanciate it for us based on the data returned by the gateway.

```python
@strawberry.federation.type(keys=["id"])
class Book:
    id: strawberry.ID
    reviews: List[Review] = strawberry.field(resolver=get_reviews)
```

</Note>

## Let's run our services

Before starting Apollo Router to compose our schemas we need to run the
services.

In two terminal windows, run the following commands:

```shell
cd books
strawberry server --port 3500 app
```

```shell
cd reviews
strawberry server --port 3000 app
```

## Apollo Router

Now we have our services up and running, we need to configure a gateway to
consume our services. Apollo provides a router that can be used for this.

Before continuing we'll need to install Apollo Router by following
[their installation guide](https://www.apollographql.com/docs/router/quickstart/)
and we'll need to
[install Apollo's CLI](https://www.apollographql.com/docs/rover/getting-started)
to compose the schema.

<Note>

Composing the schema means combining all our service's schemas into a single
schema. The composed schema will be used by the router to route requests to the
appropriate services.

</Note>

Create a file called `supergraph.yaml` with the following contents:

```yaml
federation_version: 2
subgraphs:
  reviews:
    routing_url: http://localhost:3000
    schema:
      subgraph_url: http://localhost:3000

  books:
    routing_url: http://localhost:3500
    schema:
      subgraph_url: http://localhost:3500
```

This file will be used by rover to compose the schema, which can be done with
the following command:

```shell
# Creates prod-schema.graphql or overwrites if it already exists
rover supergraph compose --config ./supergraph.yaml > supergraph-schema.graphql
```

Now that we have the composed schema, we can start the router.

```shell
./router --supergraph supergraph-schema.graphql
```

Now that router is running we can go to
[http://localhost:4000](http://localhost:4000) and try to run the following
query:

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

if everything went well we should get the following result:

```json
{
  "data": {
    "allBooks": [
      {
        "id": "1",
        "reviewsCount": 3,
        "reviews": [
          {
            "body": "A review for 1"
          },
          {
            "body": "A review for 1"
          },
          {
            "body": "A review for 1"
          }
        ]
      }
    ]
  }
}
```

We have provided a full example that you can run and tweak to play with
Strawberry and Federation. The repo is available here:
[https://github.com/strawberry-graphql/federation-demo](https://github.com/strawberry-graphql/federation-demo)

## Federated schema directives

Strawberry provides implementations for
[Apollo federation-specific GraphQL directives](https://www.apollographql.com/docs/federation/federated-types/federated-directives/)
up to federation spec v2.7.

Some of these directives may not be necessary to directly include in your code,
and are accessed through other means.

- `@interfaceObject` (for more details, see
  [Extending interfaces](https://strawberry.rocks/docs/federation/entity-interfaces))
- `@key` (for more details, see
  [Entities (Apollo Federation)](https://strawberry.rocks/docs/federation/entities))
- `@link` (is automatically be added to the schema when any other federated
  schema directive is used)

Other directives you may need to specifically include when relevant.

- `@composeDirective`
- `@external`
- `@inaccessible`
- `@override`
- `@provides`
- `@requires`
- `@shareable`
- `@tag`
- `@authenticated`
- `@requiresScopes`
- `@policy`

For example, adding the following directives:

```python
import strawberry
from strawberry.federation.schema_directives import Inaccessible, Shareable, Tag


@strawberry.type(directives=[Key(fields="id"), Tag(name="experimental")])
class Book:
    id: strawberry.ID


@strawberry.type(directives=[Shareable()])
class CommonType:
    foo: str
    woops: bool = strawberry.field(directives=[Inaccessible()])
```

Will result in the following GraphQL schema:

```graphql
schema
  @link(
    url: "https://specs.apollo.dev/federation/v2.7"
    import: ["@key", "@inaccessible", "@shareable", "@tag"]
  ) {
  query: Query
  mutation: Mutation
}

type Book @tag(name: "experimental") @key(fields: "id", resolveable: true) {
  id: ID!
}

type CommonType @shareable {
  foo: String!
}
```

## Additional resources

[Apollo Federation Quickstart](https://www.apollographql.com/docs/federation/quickstart/setup/)
