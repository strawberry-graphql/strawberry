---
title: MaskErrors
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
    ]
)
```

## API reference:

```python
class MaskErrors(should_mask_error=default_should_mask_error, error_message="Unexpected error.", status_code_hook=None)
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

#### `status_code_hook: Callable[[GraphQLError, ExecutionContext], None] = None`

Predicate function to update the `Response`, which can be accessed from the 
`Execution Context` given. This allows you to dynamically set the `Response.status_code` 
based on the `original_error` attribute from the `GraphQLError`.

<Note>

`status_code_hook` defaults to `None`.

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
    ]
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
    ]
)
```

</details>


<details>
  <summary>Change response status code dynamically</summary>

```python
import strawberry
from strawberry.extensions import MaskErrors
from graphql.error import GraphQLError
from strawberry.types import ExecutionContext

VISIBLE_ERROR_STATUS_CODE = 400
HIDDEN_ERROR_STATUS_CODE = 500

class VisibleError(Exception):
    pass

def should_mask_error(error: GraphQLError) -> bool:
    original_error = error.original_error
    if original_error and isinstance(
        original_error, (VisibleError, PermissionError)
    ):
        return False
    return True

def status_code_hook(error: GraphQLError, execution_context: ExecutionContext) -> None:
    """Getting the response from the execution context depends on your context configuration.
    This example uses the default FastAPI config."""
    response = execution_context.context['response'] # change depending on your context config
    if response:
        if should_mask_error(error):
            response.status_code = HIDDEN_ERROR_STATUS_CODE
        else:
            response.status_code = VISIBLE_ERROR_STATUS_CODE


schema = strawberry.Schema(
    Query,
    extensions=[
        MaskErrors(should_mask_error=should_mask_error, status_code_hook=status_code_hook),
    ]
)
```

</details>