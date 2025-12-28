---
title: Scalars
---

# Scalars

Scalar types represent concrete values at the leaves of a query. For example in
the following query the `name` field will resolve to a scalar type (in this case
it's a `String` type):

<CodeGrid>

```graphql "name"
{
  user {
    name
  }
}
```

```json '"name": "Patrick"'
{
  "data": {
    "user": {
      "name": "Patrick"
    }
  }
}
```

</CodeGrid>

There are several built-in scalars, and you can define custom scalars too.
([Enums](/docs/types/enums) are also leaf values.) The built in scalars are:

- `String`, maps to Python’s `str`
- `Int`, a signed 32-bit integer, maps to Python’s `int`
- `Float`, a signed double-precision floating-point value, maps to Python’s
  `float`
- `Boolean`, true or false, maps to Python’s `bool`
- `ID`, a specialised `String` for representing unique object identifiers
- `Date`, an ISO-8601 encoded
  [date](https://docs.python.org/3/library/datetime.html#date-objects)
- `DateTime`, an ISO-8601 encoded
  [datetime](https://docs.python.org/3/library/datetime.html#datetime-objects)
- `Time`, an ISO-8601 encoded
  [time](https://docs.python.org/3/library/datetime.html#time-objects)
- `Decimal`, a
  [Decimal](https://docs.python.org/3/library/decimal.html#decimal.Decimal)
  value serialized as a string
- `UUID`, a [UUID](https://docs.python.org/3/library/uuid.html#uuid.UUID) value
  serialized as a string
- `Void`, always null, maps to Python’s `None`
- `JSON`, a JSON value as specified in
  [ECMA-404](https://ecma-international.org/publications-and-standards/standards/ecma-404/)
  standard, maps to Python’s `dict`
- `Base16`, `Base32`, `Base64`, represents hexadecimal strings encoded with
  `Base16`/`Base32`/`Base64`. As specified in
  [RFC4648](https://datatracker.ietf.org/doc/html/rfc4648.html). Maps to
  Python’s `str`

Fields can return built-in scalars by using the Python equivalent:

<CodeGrid>

```python
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
```

```graphql
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

</CodeGrid>

Scalar types can also be used as inputs:

```python 'date_input: datetime.date'
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
from strawberry.schema.config import StrawberryConfig

Base64 = NewType("Base64", bytes)


@strawberry.type
class Query:
    @strawberry.field
    def base64(self) -> Base64:
        return Base64(b"hi")


schema = strawberry.Schema(
    Query,
    config=StrawberryConfig(
        scalar_map={
            Base64: strawberry.scalar(
                name="Base64",
                serialize=lambda v: base64.b64encode(v).decode("utf-8"),
                parse_value=lambda v: base64.b64decode(v.encode("utf-8")),
            )
        }
    ),
)

result = schema.execute_sync("{ base64 }")

assert result.data == {"base64": "aGk="}
```

<Note>

The `Base16`, `Base32` and `Base64` scalar types are available in
`strawberry.scalars`

```python
from strawberry.scalars import Base16, Base32, Base64
```

</Note>

## Example: Custom Object Scalar

Suppose we would like to use a Pillow `Image` as a scalar that serializes
to/from base64-encoded bytes:

```python
import base64
from io import BytesIO

from PIL import Image

import strawberry
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class Query:
    @strawberry.field
    def generate_image(self) -> Image.Image:
        # Create a simple 100x100 red image
        return Image.new("RGB", (100, 100), color="red")


schema = strawberry.Schema(
    Query,
    config=StrawberryConfig(
        scalar_map={
            Image.Image: strawberry.scalar(
                name="Image",
                description="A Pillow Image, serialized as base64-encoded PNG",
                serialize=lambda img: base64.b64encode(img.tobytes("png")).decode(
                    "utf-8"
                ),
                parse_value=lambda v: Image.open(BytesIO(base64.b64decode(v))),
            )
        }
    ),
)
```

This generates the following schema:

```graphql
"""
A Pillow Image, serialized as base64-encoded PNG
"""
scalar Image

type Query {
  generateImage: Image!
}
```

<CodeGrid>

```graphql
query {
  generateImage
}
```

```json
{
  "data": {
    "generateImage": "iVBORw0KGgoAAAANSUhEUgAAAAE..."
  }
}
```

</CodeGrid>

## Example: NewType Scalar

Suppose we would like to have a type-safe `Currency` scalar based on `Decimal`:

```python
from decimal import Decimal
from typing import NewType

import strawberry
from strawberry.schema.config import StrawberryConfig

# Define a NewType for currency - this is a proper type that type checkers understand
Currency = NewType("Currency", Decimal)


@strawberry.type
class Query:
    @strawberry.field
    def price(self) -> Currency:
        return Currency("19.99")


schema = strawberry.Schema(
    Query,
    config=StrawberryConfig(
        scalar_map={
            Currency: strawberry.scalar(
                name="Currency",
                description="A monetary value with 2 decimal places",
                serialize=lambda v: str(v.quantize(Decimal("0.01"))),
                parse_value=lambda v: Currency(v).quantize(Decimal("0.01")),
            )
        }
    ),
)
```

This generates the following schema:

```graphql
"""
A monetary value with 2 decimal places
"""
scalar Currency

type Query {
  price: Currency!
}
```

<CodeGrid>

```graphql
query {
  price
}
```

```json
{
  "data": {
    "price": "19.99"
  }
}
```

</CodeGrid>

<Note>

The `JSON` scalar type is available in `strawberry.scalars`:

```python
from strawberry.scalars import JSON
```

</Note>

## Overriding built-in scalars

To override the behaviour of the built-in scalars, you can pass a `scalar_map`
in your schema config.

Here is a full example of replacing the built-in `DateTime` scalar with one that
serializes all datetimes as Unix timestamps:

```python
from datetime import datetime, timezone
import strawberry
from strawberry.schema.config import StrawberryConfig


@strawberry.type
class Query:
    @strawberry.field
    def current_time(self) -> datetime:
        return datetime.now()


schema = strawberry.Schema(
    Query,
    config=StrawberryConfig(
        scalar_map={
            datetime: strawberry.scalar(
                name="DateTime",
                serialize=lambda value: int(value.timestamp()),
                parse_value=lambda value: datetime.fromtimestamp(
                    int(value), timezone.utc
                ),
            ),
        }
    ),
)
result = schema.execute_sync("{ currentTime }")
assert result.data == {"currentTime": 1628683200}
```

### Replacing datetime with the popular `pendulum` library

To override with a pendulum instance you'd want to serialize and parse_value
like the above example. Let's throw them in a class this time.

In addition we'll be using the `Union` clause to combine possible input types.
Since pendulum isn't typed yet, we'll have to silence mypy's errors using
`# type: ignore`

```python
import pendulum
from datetime import datetime
from typing import Union

import strawberry
from strawberry.schema.config import StrawberryConfig


def serialize_datetime(dt: Union[pendulum.DateTime, datetime]) -> str:  # type: ignore
    try:
        return dt.isoformat()
    except ValueError:
        return dt.to_iso8601_string()  # type: ignore


def parse_datetime(value: str) -> Union[pendulum.DateTime, datetime]:  # type: ignore
    return pendulum.parse(value)  # type: ignore


schema = strawberry.Schema(
    Query,
    config=StrawberryConfig(
        scalar_map={
            datetime: strawberry.scalar(
                name="DateTime",
                description="A date and time",
                serialize=serialize_datetime,
                parse_value=parse_datetime,
            ),
        }
    ),
)
```

## BigInt (64-bit integers)

Python integers have arbitrary precision (no size limit). However, the GraphQL
spec limits integers to 32-bit signed values (approximately ±2 billion).

This will inevitably raise errors. Instead of using strings on the client as a
workaround, you could use the following approach:

```python
from typing import NewType, Union

import strawberry
from strawberry.schema.config import StrawberryConfig

BigInt = NewType("BigInt", int)


@strawberry.type
class Query:
    @strawberry.field
    def large_number(self) -> BigInt:
        return BigInt(9007199254740993)


schema = strawberry.Schema(
    Query,
    config=StrawberryConfig(
        scalar_map={
            BigInt: strawberry.scalar(
                name="BigInt",
                description="BigInt field",
                serialize=lambda v: int(v),
                parse_value=lambda v: str(v),
            ),
        }
    ),
)
```

You can adapt your schema to automatically use this scalar for all integers by
adding `int` to the `scalar_map`:

<Tip>
  Only use this override if you expect most of your integers to be 64-bit. Since
  most GraphQL schemas follow standardized design patterns and most clients
  require additional effort to handle all numbers as strings, it makes more
  sense to reserve BigInt for numbers that actually exceed the 32-bit limit. You
  can achieve this by annotating `BigInt` instead of `int` in your resolvers
  handling large python integers.
</Tip>

```python
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    config=StrawberryConfig(
        scalar_map={
            int: strawberry.scalar(
                name="BigInt",
                serialize=lambda v: int(v),
                parse_value=lambda v: str(v),
            ),
        }
    ),
)
```
