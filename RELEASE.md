Release type: patch

Add support for piping `StrawberryUnion` and `None` when annotating types.

For example:
```python
@strawberry.type
class Cat:
    name: str

@strawberry.type
class Dog:
    name: str

Animal = strawberry.union("Animal", (Cat, Dog))

@strawberry.type
class Query:
    animal: Animal | None # This line no longer triggers a TypeError
```
