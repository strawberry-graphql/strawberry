---
title: Fields
path: /docs/types/fields
---

# Fields

## Usage

GraphQL fields can be declared in Strawberry using either
[dataclass][dataclass_docs]-style fields, or using the `strawberry.field`
function. The function can be used as a decorator around a resolver for the
field, or directly provided to the function directly using its `resolver`
argument.

[dataclass_docs]: https://docs.python.org/3/library/dataclasses.html

### Dataclass-style fields:

```python
@strawberry.type
class CoolType:
    my_field: int
    my_other_field: float = 1.2
```

### `strawberry.field` as a function:

```python
@strawberry.type
class CoolType:
    def my_resolver(self) -> int:
        return 4

    my_field = strawberry.field(resolver=my_resolver)
    my_other_field: int = strawberry.field(resolver=my_resolver)
```

### `strawberry.field` as a decorator

```python
@strawberry.type
class CoolType:
    @strawberry.field
    def my_field(self):
        return 4
```

## `strawberry.field` parameters

`strawberry.field` provides a number of useful parameters to express GraphQL
functionality:

- [`resolver`](#resolver): `Optional[Callable]`
- [`name`:](#name) `Optional[str]`
- [`is_subscription`](#is_subscription): `bool`
- [`description`](#description): `Optional[str]`
- [`permission_classes`](#permission_classes):
  `Optional[List[Type[BasePermission]]]`
- [`federation`](#federation): `Optional[FederationFieldParams]`

### `resolver`

type: `Optional[Callable]`  
default: `None`

The most commonly used parameter, it allows for a resolver to be added to a
field. This parameter is also filled when using `strawberry.field` as a
decorator.

### `name`

type: `Optional[str]`  
default: `None`

By default the GraphQL schema gets its field name from either the Python field,
or the wrapped resolver function if `strawberry.field` is used as a decorator.
This parameter is used to manually set the field name on the schema.

Note that Strawberry will typically camel-case the field name when creating the
field on the schema. If the `name` argument is supplied, it is left as-is and
not camel-cased.

### `is_subscription`

type: `bool`  
default: `False`

TODO

### `description`

type: `Optional[str]`  
default: `None`

TODO

### `permission_classes`

type: `Optional[List[Type[BasePermission]]]`  
default: `None`

TODO

### `federation`

type: `Optional[FederationFieldParams]`  
default: `None`

TODO

## Typing

Strawberry must be able to infer the type of the field—either from the field
itself, or from the return type of the resolver.

```python
@strawberry.type
class CoolType:
    my_field: int = strawberry.field
```

If these two sources of typing differ, an exception is thrown.

```python
@strawberry.type
class CoolType:

    def float_resolver(self) -> float:
        ...

    my_field: int = strawberry.field(resolver=float_resolver)
```

## Exceptions

TODO

---

TODO: Describe how queries and fields are the same; link here from query docs
TODO: What happens when the field has no resolver or default value
