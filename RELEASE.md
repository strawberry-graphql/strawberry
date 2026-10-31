---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes union fields not
    calling a member type's custom `resolve_type`, so interfaces with custom
    type resolution now work the same way whether returned directly or
    through a union. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes union fields not
    calling a member type's custom `resolve_type`, so interfaces with custom
    type resolution now behave consistently whether a field returns the
    interface directly or a union that includes it.
---

This release fixes union fields not calling a custom `resolve_type`
classmethod defined on (or inherited by) one of the union's member types.

Previously, a type's `resolve_type` classmethod was only consulted when the
type (or an interface it implements) was used directly as a field's return
type. When the same type appeared as a member of a `Union[...]` field instead,
`resolve_type` was silently ignored, and Strawberry fell back to structural
matching and `is_type_of`, which can't always tell apart interface
implementations that share the same fields:

```python
import strawberry
from typing import Annotated, Union


@strawberry.interface
class Fruit:
    kind: str

    @classmethod
    def resolve_type(cls, obj, *args, **kwargs) -> str:
        return "Apple" if obj.kind == "Apple" else "Banana"


@strawberry.type
class Apple(Fruit): ...


@strawberry.type
class Banana(Fruit): ...


FruitUnion = Annotated[Union[Apple, Banana], strawberry.union("FruitUnion")]


@strawberry.type
class Query:
    @strawberry.field
    def fruit(self) -> FruitUnion:
        return Fruit(kind="Banana")
```

Querying `fruit { __typename }` now correctly resolves to `Banana`. Previously
Strawberry either raised `UnallowedReturnTypeForUnion` or, depending on the
member types' automatically-derived `is_type_of`, silently resolved to the
wrong member.
