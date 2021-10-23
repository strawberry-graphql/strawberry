Release type: patch

Field definition uses output of `default_factory` as the GraphQL `default_value`.
```python
a_field: list[str] = strawberry.field(default_factory=list)
```
```graphql
aField: [String!]! = []
```
