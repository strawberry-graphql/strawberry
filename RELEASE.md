---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes `strawberry.cast` when
    used with unions of types that don't implement an interface. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes `strawberry.cast` when
    used with unions of types that don't implement an interface, so ORM objects
    returned from a union field now resolve to the type you cast them to.
---

This release fixes `strawberry.cast` when used with unions.

`strawberry.cast` is the supported way to tell Strawberry which type an object
should resolve to when returning something that isn't an instance of any of the
union's types, such as a Django, Pydantic or SQLAlchemy object. It worked for
interfaces, and for unions whose types implement an interface, but was ignored
for unions of plain types, which failed with `WrongReturnTypeForUnion`:

```python
@strawberry.type
class Apple:
    name: str


@strawberry.type
class Banana:
    name: str


Fruit = Annotated[Apple | Banana, strawberry.union("Fruit")]


@strawberry.type
class Query:
    @strawberry.field
    def fruits(self) -> list[Fruit]:
        return [
            strawberry.cast(Banana, banana_model),
            strawberry.cast(Apple, apple_model),
        ]
```

Each item now resolves to the type it was cast to, instead of raising an error.
