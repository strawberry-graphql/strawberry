Release type: minor

This release adds `strawberry.input_mutation` as a way to make it easier to create
mutations that receive a single input type called `input`, while still being able
to define the arguments of that input in the resolver itself.

The following example:

```python
@strawberry.type
class Fruit:
    id: strawberry.ID
    name: str
    weight: float


@strawberry.type
class Mutation:
    @strawberry.input_mutation
    def update_fruit_weight(
        self,
        info: Info,
        id: strawberry.ID,
        weight: float,
    ) -> Fruit:
        fruit = ...  # retrieve the fruit with the given ID
        fruit.weight = weight
        ...  # maybe save the fruit in the database
        return fruit
```

Would generate a schema like this:

```graphql
input CreateFruitInput {
  id: ID!
  weight: Float!
}

type Fruit {
  id: ID!
  name: String!
  weight: Float!
}

type Mutation {
  updateFruitWeight(input: CreateFruitInput!): Fruit!
}
```

That pattern makes it easier to include/remove arguments without breaking the
whole API, which could happen when using positional arguments.
