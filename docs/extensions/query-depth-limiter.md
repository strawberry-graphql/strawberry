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
    ],
)
```

## API reference:

```python
class QueryDepthLimiter(max_depth, ignore=None, callback=None):
    ...
```

#### `max_depth: int`

The maximum allowed depth for any operation in a GraphQL document.

#### `ignore: Optional[List[IgnoreType]]`

Stops recursive depth checking based on user-defined rule like a field name
or a field name and a set of field arguments.

The fundamental way in which the limiter judges whether to ignore a specific
field is by using the `FieldAttributeRuleType` in comparing the attribute of
the field to a user-defined rule. This rule takes the form of a string that
exactly matches the attribute, a regular expression that matches the attribute,
or a function that returns a boolean when operating on the attribute.

When providing your custom rules to the `QueryDepthLimiter` through the
`ignore` field, they can be an variable that satisfies `FieldAttributeRuleType`
or a `FieldRule` dataclass. The `FieldRule` dataclass is a wrapper around
`FieldAttributeRuleType` that allows you to specify the `field_name` as
a variable that satisfies `FieldAttributeRuleType` and the field_arguments
as an optional dictionary that maps individual arguments to a
list of variables that satisfy `FieldAttributeRuleType`.

The `IgnoreType` specified in the `ignore` field can be either a `FieldAttributeRuleType`
or a `FieldRule`. The list of ignores can contain any combination of variables satisfying
`FieldAttributeRuleType` or being instances of `FieldRule`.

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
        QueryDepthLimiter(max_depth=2, ignore=["user"]),
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
        QueryDepthLimiter(max_depth=2, ignore=[re.compile(r".*favourite.*")]),
    ],
)

# This query succeeds because a field that contains `favourite` is ignored
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
            max_depth=2, ignore=[lambda field_name: field_name == "user"]
        ),
    ],
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

</details>

<detail>
  <summary>Ignoring fields with FieldRule and no arguments</summary>

```python
import strawberry
from strawberry.extensions import FieldRule, QueryDepthLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        QueryDepthLimiter(
            max_depth=2,
            ignore=[
                FieldRule(
                    field_name="user",
                )
            ],
        ),
    ],
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

</details>

<details>
  <summary>Ignoring fields with FieldRule and arguments</summary>

```python
import strawberry
from strawberry.extensions import FieldRule, QueryDepthLimiter

schema = strawberry.Schema(
    Query,
    extensions=[
        QueryDepthLimiter(
            max_depth=2,
            ignore=[
                FieldRule(
                    field_name=lambda field_name: field_name == "book",
                )
            ],
        ),
    ],
)

# This query succeeds because the `book` field
# with an argument of id: 1 is ignored
schema.execute(
    """
  query NotTooDeep {
    book(id: "1") {
      author {
        publishedBooks {
          title
        }
      }
    }
  }
"""
)
```

</details>
