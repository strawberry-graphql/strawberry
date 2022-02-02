Release type: patch

This release fixes an issue with the name generation for nested generics,
the following:

```python
T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

@strawberry.type
class Value(Generic[T]):
    value: T

@strawberry.type
class DictItem(Generic[K, V]):
    key: K
    value: V

@strawberry.type
class Query:
    d: Value[List[DictItem[int, str]]]
```

now yields the correct schema:

```graphql
type IntStrDictItem {
  key: Int!
  value: String!
}

type IntStrDictItemListValue {
  value: [IntStrDictItem!]!
}

type Query {
  d: IntStrDictItemListValue!
}
```
