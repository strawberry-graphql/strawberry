---
title: Mutations
---

# Mutations

As opposed to queries, mutations in GraphQL represent operations that modify server-side
data and/or cause side effects on the server. For example, you can have a mutation that
adds a book instance or a mutation that sends an email. Like in queries, they accept
parameters, can return data or include nested fields as well. This can be useful for
fetching the new state of an object after an update.

Let's improve our books project from the [Getting started tutorial](docs/index.md) and implement a mutation that is supposed to add a book:

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
function. Here we create a `addBook` mutation that accept a title and an author and
returns a `Book` type.

We would send the following GraphQL document to our server to execute the mutation:

```graphql
addBook(title: "The Little Prince", author: "Antoine de Saint-Exupéry")
```

The `addBook` mutation is a simplified example. In a real-world application we usually
want to return more information if an error occurs.

You can checkout our documentation on
[dealing with errors](/docs/guides/errors#expected-errors) to learn how to return a
union of types in mutation.
