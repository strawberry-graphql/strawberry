---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes classmethod resolvers
    inherited by subclasses, which now get the subclass as cls instead of the
    class that defined them. https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes resolvers defined with
    @classmethod and @staticmethod on types that are subclassed: inherited
    classmethods now get the subclass as cls, both when resolving a query and
    when called from Python, and inherited staticmethods can be called on
    instances of the subclass.
---

This release fixes classmethod resolvers inherited by a subclass being called
with the class that defined them as `cls`, instead of the subclass. For example,
`{ dog { says } }` now returns `"Dog says woof"`, and so does `Dog.says()`:

```python
from typing import ClassVar

import strawberry


@strawberry.type
class Animal:
    sound: ClassVar[str] = "..."

    @strawberry.field
    @classmethod
    def says(cls) -> str:
        return f"{cls.__name__} says {cls.sound}"


@strawberry.type
class Dog(Animal):
    sound: ClassVar[str] = "woof"
```

`cls` is now always the type using the field, both when resolving a query and
when the resolver is called from Python. This includes types implementing an
interface, subclasses of generic types, types created with `merge_types`, and
fields reused in another type, like with `create_type` or with an `Annotated`
alias used by several types. A classmethod resolver reused in another type
therefore no longer sees the class attributes of the type that defined it.

To do this, each type gets its own copy of an inherited field with a classmethod
resolver, so the field in `Dog.__strawberry_definition__` is no longer the same
object as the one in `Animal.__strawberry_definition__`, or as the one that
`dataclasses.fields(Dog)` returns, which stays bound to `Animal`. The copy is
made with `copy.copy`, like the copies Strawberry already makes of the fields of
generic types, so custom `StrawberryField` subclasses with their own state need
to implement `__copy__` to keep it.

It also fixes inherited staticmethod resolvers called on an instance of the
subclass, like `Dog().helper()`, which raised a `TypeError`.
