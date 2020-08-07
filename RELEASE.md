Release type: patch

Support for `default_value` on inputs.

Usage:
```python
class MyInput:
    s: Optional[str] = None
    i: int = 0
```
```graphql
input MyInput {
  s: String = null
  i: Int! = 0
}
```