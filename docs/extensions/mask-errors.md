---
title: Mask Errors
summary: Hide error messages from the client.
tags: security
---

# `MaskErrors`

This extension hides error messages from the client to prevent exposing
sensitive details. By default it masks all errors raised in any field resolver.

## Usage example:

```python
import strawberry
from strawberry.extensions import MaskErrors

schema = strawberry.Schema(
    Query,
    extensions=[
        MaskErrors(),
    ],
)
```

## API reference:

```python
class MaskErrors(
    should_mask_error=default_should_mask_error, error_message="Unexpected error."
): ...
```

#### `should_mask_error: Callable[[GraphQLError], bool] = default_should_mask_error`

Predicate function to check if a GraphQLError should be masked or not. Use the
`original_error` attribute to access the original error that was raised in the
resolver.

<Note>

The `default_should_mask_error` function always returns `True`.

</Note>

#### `error_message: str = "Unexpected error."`

The error message to display to the client when there is an error.

## More examples:

<details>
  <summary>Hide some exceptions</summary>

```python
import strawberry
from strawberry.extensions import MaskErrors
from graphql.error import GraphQLError


class VisibleError(Exception):
    pass


def should_mask_error(error: GraphQLError) -> bool:
    original_error = error.original_error
    if original_error and isinstance(original_error, VisibleError):
        return False

    return True


schema = strawberry.Schema(
    Query,
    extensions=[
        MaskErrors(should_mask_error=should_mask_error),
    ],
)
```

</details>

<details>
  <summary>Change error message</summary>

```python
import strawberry
from strawberry.extensions import MaskErrors

schema = strawberry.Schema(
    Query,
    extensions=[
        MaskErrors(error_message="Oh no! An error occured. Very sorry about that."),
    ],
)
```

</details>
