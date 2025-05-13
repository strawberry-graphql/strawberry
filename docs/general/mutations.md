---
title: Mutations
---

# Mutations

As opposed to queries, mutations in GraphQL represent operations that modify
server-side data and/or cause side effects on the server. For example, you can
have a mutation that creates a new instance in your application or a mutation
that sends an email. Like in queries, they accept parameters and can return
anything a regular field can, including new types and existing object types.
This can be useful for fetching the new state of an object after an update.

Let's improve our books project from the [Getting started tutorial](../index.md)
and implement a mutation that is supposed to add a book:

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
        print(f"Adding {title} by {author}")

        return Book(title=title, author=author)


schema = strawberry.Schema(query=Query, mutation=Mutation)
```

Like queries, mutations are defined in a class that is then passed to the Schema
function. Here we create an `addBook` mutation that accepts a title and an
author and returns a `Book` type.

We would send the following GraphQL document to our server to execute the
mutation:

```graphql
mutation {
  addBook(title: "The Little Prince", author: "Antoine de Saint-Exupéry") {
    title
  }
}
```

The `addBook` mutation is a simplified example. In a real-world application
mutations will often need to handle errors and communicate those errors back to
the client. For example we might want to return an error if the book already
exists.

You can checkout our documentation on
[dealing with errors](/docs/guides/errors#expected-errors) to learn how to
return a union of types from a mutation.

## Mutations without returned data

It is also possible to write a mutation that doesn't return anything.

This is mapped to a `Void` GraphQL scalar, and always returns `null`

<CodeGrid>
```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    def restart() -> None:
        print(f"Restarting the server")
```

```graphql
type Mutation {
  restart: Void
}
```

</CodeGrid>

<Note>

Mutations with void-result go against
[this community-created guide on GQL best practices](https://graphql-rules.com/rules/mutation-payload).

</Note>

## The input mutation extension

It is usually useful to use a pattern of defining a mutation that receives a
single [input type](../types/input-types) argument called `input`.

Strawberry provides a helper to create a mutation that automatically creates an
input type for you, whose attributes are the same as the args in the resolver.

For example, suppose we want the mutation defined in the section above to be an
input mutation. We can add the `InputMutationExtension` to the field like this:

```python
from strawberry.field_extensions import InputMutationExtension


@strawberry.type
class Mutation:
    @strawberry.mutation(extensions=[InputMutationExtension()])
    def update_fruit_weight(
        self,
        info: strawberry.Info,
        id: strawberry.ID,
        weight: Annotated[
            float,
            strawberry.argument(description="The fruit's new weight in grams"),
        ],
    ) -> Fruit:
        fruit = ...  # retrieve the fruit with the given ID
        fruit.weight = weight
        ...  # maybe save the fruit in the database
        return fruit
```

That would generate a schema like this:

```graphql
input UpdateFruitWeightInput {
  id: ID!

  """
  The fruit's new weight in grams
  """
  weight: Float!
}

type Mutation {
  updateFruitWeight(input: UpdateFruitWeightInput!): Fruit!
}
```

## Nested mutations

To avoid a graph becoming too large and to improve discoverability, it can be
helpful to group mutations in a namespace, as described by
[Apollo's guide on Namespacing by separation of concerns](https://www.apollographql.com/docs/technotes/TN0012-namespacing-by-separation-of-concern/).

```graphql
type Mutation {
  fruit: FruitMutations!
}

type FruitMutations {
  add(input: AddFruitInput): Fruit!
  updateWeight(input: UpdateFruitWeightInput!): Fruit!
}
```

Since all GraphQL operations are fields, we can define a `FruitMutation` type
and add mutation fields to it like we could add mutation fields to the root
`Mutation` type.

```python
import strawberry


@strawberry.type
class FruitMutations:
    @strawberry.mutation
    def add(self, info, input: AddFruitInput) -> Fruit: ...

    @strawberry.mutation
    def update_weight(self, info, input: UpdateFruitWeightInput) -> Fruit: ...


@strawberry.type
class Mutation:
    @strawberry.field
    def fruit(self) -> FruitMutations:
        return FruitMutations()
```

<Note>
Fields on the root `Mutation` type are resolved serially. Namespace types introduce the potential for mutations to be resolved asynchronously and in parallel because the mutation fields that mutate data are no longer at the root level.

To guarantee serial execution when namespace types are used, clients should use
aliases to select the root mutation field for each mutation. In the following
example, once `addFruit` execution is complete, `updateFruitWeight` begins.

```graphql
mutation (
  $addFruitInput: AddFruitInput!
  $updateFruitWeightInput: UpdateFruitWeightInput!
) {
  addFruit: fruit {
    add(input: $addFruitInput) {
      id
    }
  }

  updateFruitWeight: fruit {
    updateWeight(input: $updateFruitWeightInput) {
      id
    }
  }
}
```

For more details, see
[Apollo's guide on Namespaces for serial mutations](https://www.apollographql.com/docs/technotes/TN0012-namespacing-by-separation-of-concern/#namespaces-for-serial-mutations)
and
[Rapid API's Interactive Guide to GraphQL Queries: Aliases and Variables](https://rapidapi.com/guides/graphql-aliases-variables).

</Note>
