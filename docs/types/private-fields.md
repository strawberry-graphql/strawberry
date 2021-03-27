---
title: Private Fields
---

## Using Private type hint

Fields can be hidden from the schema by using the Private type hint, like so:

```python+schema
import strawberry

@strawberry.type
class Post:
    uid: strawberry.Private[str]
    title: str
    description: str
---

type Post {
  title: String!
  description: String!
}
```

## Using private_fields variable

Fields may also be hidden from the schema by passing a private_fields variable to
strawberry.type, like so:

```python+schema
import strawberry

@strawberry.type(private_fields=["uid"])
class Post:
    uid: str
    title: str
    description: str
---

type Post {
  title: String!
  description: String!
}
```
