Release type: patch

Mutable default values are frozen to support lists and objects.
```python
@strawberry.field
def search(self, arg: List[int] = [], input: MyInput = {}) -> int:
    ...
```
