---
title: QueryDepthLimiter
summary: Add a validator to limit the query depth of GraphQL operations.
tags: security
---

# `QueryDepthLimiter`

This extension adds a validator to limit the query depth of GraphQL operations.

## Usage example:

```python
import strawberry
from strawberry.extensions import QueryDepthLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        QueryDepthLimiter(max_depth=10),
    ]
)
```

## API reference:

```python
class QueryDepthLimiter(max_depth, ignore=None, callback=None)
```

#### `max_depth: int`

The maximum allowed depth for any operation in a GraphQL document.

#### `ignore: Optional[List[IgnoreType]]`

Stops recursive depth checking based on a field name.
Either a string or regexp to match the name, or a function that returns
a boolean.

#### `callback: Optional[Callable[[Dict[str, int]], None]`

Called each time validation runs. Receives a dictionary which is a
map of the depths for each operation.

## More examples:

<details>
  <summary>Ignoring fields</summary>

```python
import strawberry
from strawberry.extensions import QueryDepthLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        QueryDepthLimiter(
          max_depth=2,
          ignore=["user"]
        ),
    ]
)

# This query fails
schema.execute("""
  query TooDeep {
    book {
      author {
        publishedBooks {
          title
        }
      }
    }
  }
""")

# This query succeeds because the `user` field is ignored
schema.execute("""
  query NotTooDeep {
    user {
      favouriteBooks {
        author {
          publishedBooks {
            title
          }
        }
      }
    }
  }
""")
```

</details>

<details>
  <summary>Ignoring fields with regex</summary>

```python
import re
import strawberry
from strawberry.extensions import QueryDepthLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        QueryDepthLimiter(
          max_depth=2,
          ignore=[re.compile(r".*favourite.*"]
        ),
    ]
)

# This query succeeds because an field that contains `favourite` is ignored
schema.execute("""
  query NotTooDeep {
    user {
      favouriteBooks {
        author {
          publishedBooks {
            title
          }
        }
      }
    }
  }
""")
```

</details>

<details>
  <summary>Ignoring fields with a function</summary>

```python
import strawberry
from strawberry.extensions import QueryDepthLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        QueryDepthLimiter(
          max_depth=2,
          ignore=[lambda field_name: field_name == "user"]
        ),
    ]
)

schema.execute("""
  query NotTooDeep {
    user {
      favouriteBooks {
        author {
          publishedBooks {
            title
          }
        }
      }
    }
  }
""")
```

</details>
