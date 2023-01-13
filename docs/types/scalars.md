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
- `Void`, always null, maps to Python’s `None`

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
    void: None
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
  void: Void
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
    parse_value=lambda v: base64.b64decode(v).encode("utf-8"),
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

<Note>

The `Base16`, `Base32` and `Base64` scalar types are available in `strawberry.scalars`

```python
from strawberry.scalars import Base16, Base32, Base64
```

</Note>

## Example JSONScalar

```python
import json
from typing import Any, NewType

import strawberry

JSON = strawberry.scalar(
    NewType("JSON", object),
    description="The `JSON` scalar type represents JSON values as specified by ECMA-404",
    serialize=lambda v: v,
    parse_value=lambda v: v,
)

```

Usage:

```python
@strawberry.type
class Query:
    @strawberry.field
    def data(self, info) -> JSON:
        return {"hello": {"a": 1}, "someNumbers": [1, 2, 3]}

```

```graphql+response
query ExampleDataQuery {
  data
}
---
{
  "data": {
    "hello": {
      "a": 1
    },
    "someNumbers": [1, 2, 3]
  }
}
```

<Note>

The `JSON` scalar type is available in `strawberry.scalars`

```python
from strawberry.scalars import JSON
```

</Note>

## Overriding built in scalars

To override the behaviour of the built in scalars you can pass a map of
overrides to your schema.

Here is a full example of replacing the built in `DateTime` scalar with one that
serializes all datetimes as unix timestamps:

```python
from datetime import datetime, timezone
import strawberry

# Define your custom scalar
EpochDateTime = strawberry.scalar(
    datetime,
    serialize=lambda value: int(value.timestamp()),
    parse_value=lambda value: datetime.fromtimestamp(int(value), timezone.utc),
)

@strawberry.type
class Query:
    @strawberry.field
    def current_time(self) -> datetime:
        return datetime.now()

schema = strawberry.Schema(
  Query,
  scalar_overrides={
    datetime: EpochDateTime,
  }
)
result = schema.execute_sync("{ currentTime }")
assert result.data == {"currentTime": 1628683200}
```
