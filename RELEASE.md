---
release type: minor
---

This release adds an error for undecorated subclasses of Strawberry types used
in the schema:

```python
import strawberry


@strawberry.type
class Animal:
    name: str


class Dog(Animal):  # missing @strawberry.type
    breed: str


@strawberry.type
class Query:
    dog: Dog


schema = strawberry.Schema(query=Query)
```

Python inherits the Strawberry definition of `Animal`, so `Dog` was silently
published as `Animal`, and its `breed` field was missing from the schema. The
same happened to undecorated subclasses of interfaces and input types: an
argument typed with an undecorated subclass of an input type only accepted the
parent's fields, and the resolver received an instance of the subclass that was
missing the fields declared on it.

Strawberry now raises an `UndecoratedSubclassError` pointing at the subclass
when it's used in the schema: in field and argument annotations (including in
lists, optionals and unions), lazy types, `strawberry.Schema(types=[...])` and
as the query, mutation or subscription type.

Schemas that relied on this now fail to build. To fix them, decorate the
subclass (with `@strawberry.type`, or `@strawberry.input` for input types), or
use the parent type in the annotation if you meant to publish it. Resolvers can
still return instances of undecorated subclasses of the type they're annotated
with.
