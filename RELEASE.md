---
release type: minor
---

This release fixes the annotations of Strawberry types with fields that have a
resolver: `typing.get_type_hints()` and other tools that read a type's
annotations no longer see a `StrawberryAnnotation` object for these fields.

Strawberry adds an annotation for each field with a resolver that doesn't have
one, like a `@strawberry.field` method, so that `dataclasses` creates the field.
These annotations are now removed once the type is created, so the class only
keeps the annotations you wrote:

```python
import typing

import strawberry


@strawberry.type
class User:
    name: str

    @strawberry.field
    def greeting(self) -> str:
        return f"Hi {self.name}"


typing.get_type_hints(User)  # {'name': <class 'str'>}
```

Code that read `__annotations__` to find a type's fields with a resolver can use
`strawberry.types.get_object_definition(User).fields` instead, which has all of
them.
