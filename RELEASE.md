Release type: minor

This release adds a new field extension called `InputMutationExtension`, which makes
it easier to create mutations that receive a single input type called `input`,
while still being able to define the arguments of that input on the resolver itself.

The following example:

```python
import strawberry
from strawberry.field_extensions import InputMutationExtension


@strawberry.type
class Fruit:
    id: strawberry.ID
    name: str
    weight: float


@strawberry.type
class Mutation:
    @strawberry.mutation(extensions=[InputMutationExtension()])
    def update_fruit_weight(
        self,
        info: Info,
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

Would generate a schema like this:

```graphql
input UpdateFruitInput {
  id: ID!

  """
  The fruit's new weight in grams
  """
  weight: Float!
}

type Fruit {
  id: ID!
  name: String!
  weight: Float!
}

type Mutation {
  updateFruitWeight(input: UpdateFruitInput!): Fruit!
}
```
