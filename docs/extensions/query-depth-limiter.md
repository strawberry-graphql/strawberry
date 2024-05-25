---
title: Query Depth Limiter
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
    ],
)
```

## API reference:

```python
class QueryDepthLimiter(max_depth, callback=None, should_ignore=None): ...
```

#### `max_depth: int`

The maximum allowed depth for any operation in a GraphQL document.

#### `callback: Optional[Callable[[Dict[str, int]], None]`

Called each time validation runs. Receives a dictionary which is a map of the
depths for each operation.

#### `should_ignore: Optional[Callable[[IgnoreContext], bool]]`

Called at each field to determine whether the field should be ignored or not.
Must be implemented by the user and returns `True` if the field should be
ignored and `False` otherwise.

The `IgnoreContext` class has the following attributes:

- `field_name` of type `str`: the name of the field to be compared against
- `field_args` of type
  `strawberry.extensions.query_depth_limiter.FieldArgumentsType`: the arguments
  of the field to be compared against
- `query` of type `graphql.language.Node`: the query string
- `context` of type `graphql.validation.ValidationContext`: the context passed
  to the query

This argument is injected, regardless of name, by the `QueryDepthLimiter` class
and should not be passed by the user.

Instead, the user should write business logic to determine whether a field
should be ignored or not by the attributes of the `IgnoreContext` class.

## Example with field_name:

```python
import strawberry
from strawberry.extensions import QueryDepthLimiter


def should_ignore(ignore: IgnoreContext):
    return ignore.field_name == "user"


schema = strawberry.Schema(
    Query,
    extensions=[
        QueryDepthLimiter(max_depth=2, should_ignore=should_ignore),
    ],
)

# This query fails
schema.execute(
    """
  query TooDeep {
    book {
      author {
        publishedBooks {
          title
        }
      }
    }
  }
"""
)

# This query succeeds because the `user` field is ignored
schema.execute(
    """
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
"""
)
```

## Example with field_args:

```python
import strawberry
from strawberry.extensions import QueryDepthLimiter


def should_ignore(ignore: IgnoreContext):
    return ignore.field_args.get("name") == "matt"


schema = strawberry.Schema(
    Query,
    extensions=[
        QueryDepthLimiter(max_depth=2, should_ignore=should_ignore),
    ],
)

# This query fails
schema.execute(
    """
  query TooDeep {
    book {
      author {
        publishedBooks {
          title
        }
      }
    }
  }
"""
)

# This query succeeds because the `user` field is ignored
schema.execute(
    """
  query NotTooDeep {
    user(name:"matt") {
      favouriteBooks {
        author {
          publishedBooks {
            title
          }
        }
      }
    }
  }
"""
)
```
