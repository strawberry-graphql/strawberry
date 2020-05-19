Release type: patch

Default values make input arguments nullable when the default is None.
```python
class Query:
     @strawberry.field
     def hello(self, i: int = 0, s: str = None) -> str:
         return s
```
```graphql
type Query {
  hello(i: Int! = 0, s: String): String!
}
```
