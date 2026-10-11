---
title: Undecorated Subclass Error
---

# Undecorated Subclass Error

## Description

This error is thrown when a subclass of a Strawberry type, input type or
interface is used in the schema without being decorated itself, for example the
following code will throw this error:

```python
import strawberry


@strawberry.type
class Animal:
    name: str


class Dog(Animal):
    breed: str


@strawberry.type
class Query:
    dog: Dog


schema = strawberry.Schema(query=Query)
```

This happens because `Dog` inherits the Strawberry definition of `Animal`, so it
would be published as `Animal`, without the `breed` field. For input types, the
schema would only accept the fields of the parent input type, and the fields
declared on the subclass would be missing from the instances passed to your
resolvers.

The error is raised for every type used in the schema: field and argument
annotations (including in lists, optionals and unions), lazy types, the types
passed to `strawberry.Schema(types=[...])` and the query, mutation and
subscription types.

## How to fix this error

You can fix this error by decorating the subclass, with `@strawberry.type` for
types and interfaces, or with `@strawberry.input` for input types:

```python
import strawberry


@strawberry.type
class Animal:
    name: str


@strawberry.type
class Dog(Animal):
    breed: str


@strawberry.type
class Query:
    dog: Dog


schema = strawberry.Schema(query=Query)
```

If you meant to publish the parent type, use it in the annotation instead.
Resolvers can still return instances of undecorated subclasses, as they are
instances of the parent type:

```python
import strawberry


@strawberry.type
class Animal:
    name: str


class Dog(Animal):
    def bark(self) -> str:
        return "Woof!"


@strawberry.type
class Query:
    @strawberry.field
    def animal(self) -> Animal:
        return Dog(name="Rex")


schema = strawberry.Schema(query=Query)
```
