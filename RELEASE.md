Release type: minor

This release renames the generated type from `GlobalID` to `ID` in the GraphQL
schema.

This means that when using `relay.Node`, like in this example:

```python
@strawberry.type
class Fruit(relay.Node):
    code: relay.NodeID[int]
    name: str
```

You'd create a GraphQL type that looks like this:

```graphql
type Fruit implements Node {
  id: ID!
  name: String!
}
```

while previously you'd get this:

```graphql
type Fruit implements Node {
  id: GlobalID!
  name: String!
}
```

The runtime behaviour is still the same, so if you want to use `GlobalID` in
Python code, you can still do so, for example:

```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    @staticmethod
    async def update_fruit_weight(id: relay.GlobalID, weight: float) -> Fruit:
        # while `id` is a GraphQL `ID` type, here is still an instance of `relay.GlobalID`
        fruit = await id.resolve_node(info, ensure_type=Fruit)
        fruit.weight = weight
        return fruit
```

If you want to revert this change, and keep `GlobalID` in the schema, you can
use the following configuration:

```python
schema = strawberry.Schema(
    query=Query, config=StrawberryConfig(relay_use_legacy_global_id=True)
)
```
