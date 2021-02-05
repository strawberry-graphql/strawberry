---
title: Scalars
---

# Scalars

Scalar types represent concrete values at the leaves of a query. For example
in the following query the name field will resolve to a scalar type
(in this case it's a `String` type):

```graphql+response
{
  user {
    name
  }
}
---
{
  "data": {
    "user": {
      "name": "Patrick"
    }
  }
}
```

There are several built-in scalars, and you can define custom scalars too.
([Enums](/docs/types/enums) are also leaf values.) The built in scalars are:

- `String`, maps to Python’s `str`
- `Int`, a signed 32-bit integer, maps to Python’s `int`
- `Float`, a signed double-precision floating-point value, maps to Python’s `float`
- `Boolean`, true or false, maps to Python’s `bool`
- `ID`, a specialised `String` for representing unique object identifiers
- `Date`, an ISO-8601 encoded [date](https://docs.python.org/3/library/datetime.html#date-objects)
- `DateTime`, an ISO-8601 encoded [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects)
- `Time`, an ISO-8601 encoded [time](https://docs.python.org/3/library/datetime.html#time-objects)
- `Decimal`, a [Decimal](https://docs.python.org/3/library/decimal.html#decimal.Decimal) value serialized as a string
- `UUID`, a [UUID](https://docs.python.org/3/library/uuid.html#uuid.UUID) value serialized as a string

Fields can return built-in scalars by using the Python equivalent:

```python+schema
import datetime
import decimal
import uuid
import strawberry

@strawberry.type
class Product:
    id: uuid.UUID
    name: str
    stock: int
    is_available: bool
    available_from: datetime.date
    same_day_shipping_before: datetime.time
    created_at: datetime.datetime
    price: decimal.Decimal
---
type Product {
  id: UUID!
  name: String!
  stock: Int!
  isAvailable: Boolean!
  availableFrom: Date!
  sameDayShippingBefore: Time!
  createdAt: DateTime!
  price: Decimal!
}
```

Scalar types can also be used as inputs:

```python
import datetime
import strawberry

@strawberry.type
class Query:
    @strawberry.field
    def one_week_from(self, date_input: datetime.date) -> datetime.date:
        return date_input + datetime.timedelta(weeks=1)
```

## Custom scalars

You can create custom scalars for your schema to represent specific types in
your data model. This can be helpful to let clients know what kind of data they
can expect for a particular field.

To define a custom scalar you need to give it a name and functions that tell
Strawberry how to serialize and deserialise the type.

For example here is a custom scalar type to represent a Base64 string:

```python
import base64
from typing import NewType

import strawberry

Base64 = strawberry.scalar(
    NewType("Base64", bytes),
    serialize=lambda v: base64.b64encode(v).decode("utf-8"),
    parse_value=lambda v: base64.b64decode(v.encode("utf-8")),
)

@strawberry.type
class Query:
    @strawberry.field
    def base64(self) -> Base64:
        return Base64(b"hi")

schema = strawberry.Schema(Query)

result = schema.execute_sync("{ base64 }")

assert results.data  == {"base64": "aGk="}
```
