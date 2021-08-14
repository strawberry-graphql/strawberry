---
title: Fields
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

```python+schema
@strawberry.type
class CoolType:
    my_field: int
    my_other_field: float = 1.2
---
type CoolType {
  myField: Int!
  myOtherField: Float! = 1.2
}
```

### `strawberry.field` as a function:

```python+schema
def my_resolver() -> int:
    return 4

@strawberry.type
class CoolType:
    my_field = strawberry.field(resolver=my_resolver)
    my_other_field: int = strawberry.field(resolver=my_resolver)
---
type CoolType {
  myField: Int!
  myOtherField: Int!
}
```

### `strawberry.field` as a decorator

```python+schema
@strawberry.type
class CoolType:
    @strawberry.field
    def my_field(self) -> int:
        return 4
---
type CoolType {
  myField: Int!
}
```

## `strawberry.field` parameters

`strawberry.field` provides a number of useful parameters to express GraphQL
functionality:

- [`resolver`](#resolver): `Optional[Callable]`
- [`name`:](#name) `Optional[str]`
- [`description`](#description): `Optional[str]`
- [`permission_classes`](#permission_classes):
  `Optional[List[Type[BasePermission]]]`
- [`deprecation_reason`](#deprecation_reason): `Optional[str]`
- [`default`](#default): `Optional[Any]`

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

```python+schema
@strawberry.type
class Query:
    a: str = strawberry.field(name="alpha")
---
type Query {
  alpha: String!
}
```

### `description`

> type: `Optional[str]`
> default: `None`

Add a description to the GraphQL field.

```python+schema
@strawberry.type
class Query:
    a: str = strawberry.field(description="Example")

    @strawberry.field(description="Example B")
    def b(self) -> str:
        return "I'm a resolver"
---
type Query {
  """Example"""
  a: String!

  """Example B"""
  b: String!
}
```

### `permission_classes`

> type: `Optional[List[Type[BasePermission]]]`
> default: `None`

Add permission classes to the field. See [Permissions][permission_docs] for
more information.

[permission_docs]: /docs/features/permissions

### `deprecation_reason`

> type: `Optional[str]`
> default: `None`

Add a deprecation reason to a field to indicate to the client that it should no
longer be used.

```python+schema
@strawberry.type
class Query:
    a: str = strawberry.field(deprecation_reason="Don't use me anymore. Use 'b'")
---
type Query {
  a: String! @deprecated(reason: "Don't use me anymore. Use 'b'")
}
```

## Typing

Strawberry must be able to infer the type of the field—either from the field
itself, or from the return type of the resolver.

```python
@strawberry.type
class CoolType:
    my_field: int = strawberry.field()
```

If these two sources of typing differ, an exception is thrown.

```python
@strawberry.type
class CoolType:

    def float_resolver(self) -> float:
        ...

    my_field: int = strawberry.field(resolver=float_resolver)
```

## Private fields

`strawberry.Private` allows you to pass data to a Strawberry type without it
being exposed in the GraphQL schema. Sometimes this is useful so that a resolver
on the type can return the correct value.

```python
@strawberry.type
class CoolType:
    private_stuff: strawberry.Private[dict]

    @strawberry.field
    def my_field(self) -> str:
        return self.private_stuff["my_field"]

@strawberry.type
class Query:
    @strawberry.field
    def get_my_cool_type(self) -> CoolType:
        return CoolType(private_stuff={"my_field": "Hi"})
```

<!--
## Exceptions

TODO
TODO: What happens when the field has no resolver or default value
-->
