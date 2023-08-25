---
title: PartialResultsExtension
summary: Hide error messages from the client.
tags: errors
---

# `PartialResultsExtension`

This extension enables populating an array of exceptions on the `info.context` object
that get mapped to the `errors` array after execution,
enabling responses to contain both `data` and `errors` values.
This also enables returning multiple errors in the response.

1. Add `PartialResultsExtension` to the `extensions` array in `Schema` initialization
1. In execution, add any exceptions to the `info.context.partial_errors` array

## Usage example:

```python
import strawberry
from strawberry.extensions import PartialResultsExtension

schema = strawberry.Schema(Query, extensions=[PartialResultsExtension])

# ...


@strawberry.field
def query(self, info) -> bool:
    info.context.partial_errors.append(Exception("Partial failure"))
    return True
```

Results:

```json
{
  "data": {
    "query": true
  },
  "errors": [
    {
      "message": "Partial failure"
    }
  ]
}
```

## API reference:

_No arguments_

## More examples:

<details>
  <summary>Add multiple exceptions</summary>

```python
import strawberry
from strawberry.extensions import PartialResultsExtension

schema = strawberry.Schema(Query, extensions=[PartialResultsExtension])

# ...


@strawberry.field
def query(self, info) -> bool:
    info.context.partial_errors.extend(
        [
            Exception("Failure 0"),
            Exception("Failure 1"),
            Exception("Failure 2"),
        ]
    )
    return True
```

Results:

```json
{
  "data": {
    "query": true
  },
  "errors": [
    {
      "message": "Failure 0"
    },
    {
      "message": "Failure 1"
    },
    {
      "message": "Failure 2"
    }
  ]
}
```

</details>

<details>
  <summary>Add GraphQLError with location and path detail</summary>

```python
import strawberry
from strawberry.extensions import PartialResultsExtension

schema = strawberry.Schema(Query, extensions=[PartialResultsExtension])

# ...


@strawberry.field
def query(self, info) -> bool:
    nodes = [next(n for n in info.field_nodes if n.name.value == "query")]
    info.context.partial_errors.append(
        located_error(
            Exception("Error with location and path information"),
            nodes=nodes,
            path=info.path.as_list(),
        ),
    )
    return True
```

Results:

```json
{
  "data": {
    "query": true
  },
  "errors": [
    {
      "message": "Error with location and path information",
      "location": {
        "line": 1,
        "column": 9
      },
      "path": ["query"]
    }
  ]
}
```

</details>
