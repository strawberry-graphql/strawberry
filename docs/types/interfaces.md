---
title: Interfaces
---

# Interfaces

Interfaces are abstract types which may be implemented by object types.

An interface defines fields that object types inherit when they implement it. 
These object types are then considered members of that interface.

Fields may return interface types.
However, the returned object must be resolved to a member of that interface.

## Example

Let's say a `Customer` (interface) can either be an `Individual`
(member) or a `Company` (member). Here's what that might look like in the
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

```python+schema
import strawberry

@strawberry.interface
class Customer:
    name: str
---
interface Customer {
  name: String!
}
```

<Note>

Interface class instances should not be returned without providing methods to resolve
them to a member (, as explained [here](#resolving-an-interface)). 

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

```python+schema
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
    fix: str
---
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
must be categorized as an `Individual` or `Company`. 

### Returning a member instance
To do this, you could return an instance of a member from your resolver:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def best_customer(self) -> Customer:
        return Individual(name="Patrick")
```

### Returning an interface instance
You could also return the interface directly by defining a `resolve_type`
method on the interface.

```python
import strawberry


@strawberry.interface
class Customer:
    name: str
    
    @classmethod
    async def resolve_type(cls, obj: Any, info: Info):
        return Individual.__name__ if obj.name == "Patrick" else Company.__name__

    
@strawberry.type
class Individual(Customer):
    ...


@strawberry.type
class Company(Customer):
    ...


@strawberry.type
class Query:
    @strawberry.field
    def best_customer(self) -> Customer:
        return Customer(name="Patrick")
```