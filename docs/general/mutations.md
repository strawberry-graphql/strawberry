---
title: Mutations
---

# Mutations

As opposed to queries, mutations in GraphQL represent operations that modify server-side
data and/or cause side effects on the server. For example, you can have a mutation that
creates a new instance in your application or a mutation that sends an email. Like in
queries, they accept parameters and can return anything a regular field can, including
new types and existing object types. This can be useful for fetching the new state of an
object after an update.

Let's improve our books project from the [Getting started tutorial](../index.md) and
implement a mutation that is supposed to add a book:

```python
import strawberry

# Reader, you can safely ignore Query in this example, it is required by
# strawberry.Schema so it is included here for completeness
@strawberry.type
class Query:
    @strawberry.field
    def hello() -> str:
        return "world"

@strawberry.type
class Mutation:
    @strawberry.mutation
    def add_book(self, title: str, author: str) -> Book:
        print(f'Adding {title} by {author}')

        return Book(title=title, author=author)

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

Like queries, mutations are defined in a class that is then passed to the Schema
function. Here we create an `addBook` mutation that accepts a title and an author and
returns a `Book` type.

We would send the following GraphQL document to our server to execute the mutation:

```graphql
mutation {
  addBook(title: "The Little Prince", author: "Antoine de Saint-Exupéry") {
    title
  }
}
```

The `addBook` mutation is a simplified example. In a real-world application mutations
will often need to handle errors and communicate those errors back to the client. For
example we might want to return an error if the book already exists.

You can checkout our documentation on
[dealing with errors](/docs/guides/errors#expected-errors) to learn how to return a
union of types from a mutation.

## Mutations without returned data

It is also possible to write a mutation that doesn't return anything.

This is mapped to a `Void` GraphQL scalar, and always returns `null`

```python+schema
@strawberry.type
class Mutation:
    @strawberry.mutation
    def restart() -> None:
        print(f'Restarting the server')
---
type Mutation {
  restart: Void
}
```

<Note>

Mutations with void-result go against [GQL best practices](https://graphql-rules.com/rules/mutation-payload)

</Note>
