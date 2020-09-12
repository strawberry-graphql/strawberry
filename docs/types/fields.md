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
def my_resolver() -> int:
    return 4

@strawberry.type
class CoolType:

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

> type: `Optional[Callable]`  
> default: `None`

The most commonly used parameter, it allows for a resolver to be added to a
field. This parameter is also filled when using `strawberry.field` as a
decorator.

### `name`

> type: `Optional[str]`  
> default: `None`

By default the GraphQL schema gets its field name from either the Python field,
or the wrapped resolver function if `strawberry.field` is used as a decorator.
This parameter is used to manually set the field name on the schema.

Note that Strawberry will typically camel-case the field name when creating the
field on the schema. If the `name` argument is supplied, it is left as-is and
not camel-cased.

### `is_subscription`

> type: `bool`  
> default: `False`

> **NOTE:** It's not recommended to use this argument directly. Use
> `strawberry.subscription` instead.

Mark a field as a subscription field. See [Subscriptions][subscription_docs] for
more information.

[subscription_docs]: /docs/subscriptions/

### `description`

> type: `Optional[str]`  
> default: `None`

Add a description to the GraphQL field.

```python
@strawberry.type
class Query:
    a: str = strawberry.field(description="Example")

    @strawberry.field
    def b(self) -> str:
        return "I'm a resolver"

    @strawberry.field(description="Example C")
    def c(self) -> str:
        return "I'm another resolver"
```

```graphql+response
__type(name: "Query") {
    fields {
        name
        description
    }
}
---
{
  "data": {
    "__type": {
      "fields": [
        {
          "name": "a",
          "description": "Example",
        },
        {
          "name": "b",
          "description": None,
        },
        {
          "name": "c",
          "description": "Example C",
        }
      ]
    }
  }
}
```

### `permission_classes`

> type: `Optional[List[Type[BasePermission]]]`  
> default: `None`

Add permission classes to the field. See [Permissions][permission_docs] for
more information.

[permission_docs]: /docs/features/permissions

### `federation`

> type: `Optional[FederationFieldParams]`  
> default: `None`

See [Federation][federation_docs].

[federation_docs]: /docs/features/federation

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
