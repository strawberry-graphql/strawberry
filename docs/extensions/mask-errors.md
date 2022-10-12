---
title: MaskErrors
summary: Hide error messages from the client.
tags: security
---

# `MaskErrors`

This extension hides error messages from the client to prevent exposing
sensitive details.

## Usage example:

```python
import strawberry
from strawberry.extensions import MaskErrors

schema = strawberry.Schema(
    Query,
    extensions=[
        MaskErrors(visible_errors=[MyVisibleError]),
    ]
)
```

## API reference:

```python
class MaskErrors(visible_errors, error_message="Unexpected error.")`
```

#### `visible_errors: Sequence[Type[Exception]]`

A sequence of exceptions that shouldn't be masked from the client.

<Note>

Passing an empty list will mask all errors.

</Note>

#### `error_message: str = "Unexpected error."`

The error message to display to the client when there is an error.

## More examples:

<details>
  <summary>Hide all exceptions</summary>

```python
import strawberry
from strawberry.extensions import MaskErrors

schema = strawberry.Schema(
    Query,
    extensions=[
        MaskErrors(visible_errors=[]),
    ]
)
```

</details>
