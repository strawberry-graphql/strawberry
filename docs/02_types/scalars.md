---
title: Scalars
path: /docs/types/scalars
---

# Scalars

Scalar types represent concrete values at the leaves of a query. For example in the following query the name field will resolve to a scalar type (in this case it's a string type):

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

Strawberry will automatically map the Python built in types to the corresponding
GraphQL type:

```python+schema
import strawberry

@strawberry.type
class User:
    name: str
    age: int
    like_strawberries: bool
    number_of_strawberries_eaten: float

---
type User {
  name: String!
  age: Int!
  likesStrawberries: Boolean!
  numberOfStrawberriesEaten: Float!
}
```

## Built in scalars

Strawberry also provides some built in scalars for common Python datatypes:

```python+schema
import datetime
import decimal
import uuid
import strawberry

@strawberry.type
class Product:
    id: uuid.UUID
    created_at: datetime.datetime
    available_until: datetime.date
    same_day_shipping_before: datetime.time
    price: decimal.Decimal

---
type Product {
  id: UUID!
  createdAt: DateTime!
  availableUntil: Date!
  sameDayShippingBefore: Time!
  price: Decimal!
}
```

These types can also be used as inputs to fields:

```python
import datetime
import strawberry

@strawberry.type
class Query:
    @strawberry.field
    def one_week_from(self, date_input: datetime.date) -> datetime.date:
        return date_input + datetime.timedelta(weeks=1)

schema = strawberry.Schema(query=Query)

results = schema.execute_sync("{ oneWeekFrom(dateInput: "2006-01-02") }")

assert results.data == {"oneWeekFrom": "2006-01-09"}
```

## Custom scalars

You can create custom scalars for your schema to repesent specific types in
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
