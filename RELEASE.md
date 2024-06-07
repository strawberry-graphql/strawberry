Release type: patch

This release fixes an issue when trying to retrieve specialized type vars from a
generic type that has been aliased to a name, in cases like:

```python
@strawberry.type
class Fruit(Generic[T]): ...


SpecializedFruit = Fruit[str]
```
