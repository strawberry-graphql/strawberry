---
title: Interfaces
---

# Interfaces

Interfaces are an abstract type which may be implemented by object types.

An interface has fields, but it’s never instantiated. Instead, objects may
implement interfaces, which makes them a member of that interface. Also, fields
may return interface types. When this happens, the returned object may be any
member of that interface.

For example, let's say a `Customer` (interface) can either be an `Individual`
(object) or a `Company` (object). Here's what that might look like in the
[GraphQL Schema Definition Language](https://graphql.org/learn/schema/#type-language)
(SDL):

```graphql
interface Customer {
  name: String!
}

type Company implements Customer {
  employees: [Individual!]!
  name: String!
}

type Individual implements Customer {
  employed_by: Company
  name: String!
}

type Query {
  customers: [Customer!]!
}
```

Notice that the `Customer` interface requires the `name: String!` field. Both
`Company` and `Individual` implement that field so that they can satisfy the
`Customer` interface.

When querying, you can select the fields on an interface:

```graphql
query {
  customers {
    name
  }
}
```

Whether the object is a `Company` or an `Individual`, it doesn’t matter – you
still get their name. If you want some object-specific fields, you can query
them with an
[inline fragment](https://graphql.org/learn/queries/#inline-fragments), for
example:

```graphql
query {
  customers {
    name
    ... on Individual {
      company {
        name
      }
    }
  }
}
```

Interfaces are a good choice whenever you have a set of objects that are used
interchangeably, and they have several significant fields in common. When they
don’t have fields in common, use a [Union](/docs/types/union) instead.

## Defining interfaces

Interfaces are defined using the `@strawberry.interface` decorator:

<CodeGrid>

```python
import strawberry


@strawberry.interface
class Customer:
    name: str
```

```graphql
interface Customer {
  name: String!
}
```

</CodeGrid>

<Note>

Interface classes should never be instantiated directly.

</Note>

## Implementing interfaces

To define an object type that implements an interface, the type must inherit
from the interface:

```python
import strawberry


@strawberry.type
class Individual(Customer):
    # additional fields
    ...


@strawberry.type
class Company(Customer):
    # additional fields
    ...
```

<Tip>

If you add an object type which implements an interface, but that object type
doesn’t appear in your schema as a field return type or a union member, then you
will need to add that object to the Schema definition directly.

```python
schema = strawberry.Schema(query=Query, types=[Individual, Company])
```

</Tip>

Interfaces can also implement other interfaces:

<CodeGrid>

```python
import strawberry


@strawberry.interface
class Error:
    message: str


@strawberry.interface
class FieldError(Error):
    message: str
    field: str


@strawberry.type
class PasswordTooShort(FieldError):
    message: str
    field: str
    min_length: int
```

```graphql
interface Error {
  message: String!
}

interface FieldError implements Error {
  message: String!
  field: String!
}

type PasswordTooShort implements FieldError & Error {
  message: String!
  field: String!
  minLength: Int!
}
```

</CodeGrid>

## Implementing fields

Interfaces can provide field implementations as well. For example:

```python
import strawberry


@strawberry.interface
class Customer:
    @strawberry.field
    def name(self) -> str:
        return self.name.title()
```

This resolve method will be called by objects who implement the interface.
Object classes can override the implementation by defining their own `name`
field:

```python
import strawberry


@strawberry.type
class Company(Customer):
    @strawberry.field
    def name(self) -> str:
        return f"{self.name} Limited"
```

## Resolving an interface

When a field’s return type is an interface, GraphQL needs to know what specific
object type to use for the return value. In the example above, each customer
must be categorized as an `Individual` or `Company`. To do this you need to
always return an instance of an object type from your resolver:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def best_customer(self) -> Customer:
        return Individual(name="Patrick")
```
