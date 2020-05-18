Release type: patch

Support for `default_value` on inputs and arguments.

Usage:
```python
class MyInput:
    s: Optional[str]
    i: int = 0
```
```graphql
input MyInput {
  s: String
  i: Int! = 0
}
```
