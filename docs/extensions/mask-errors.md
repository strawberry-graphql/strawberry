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


@strawberry.type
class Query:
    @strawberry.field
    def hidden_error(self) -> str:
        raise KeyError("This error will not be visible")


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
    should_mask_error=default_should_mask_error,
    error_message="Unexpected error.",
    mask_pre_execution_errors=True,
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

#### `mask_pre_execution_errors: bool = True`

Mask the errors that occur before the execution step. These are the syntax
errors of a document and the validation errors against the schema. Set the
option to `False` to send these errors to the client. The extension continues to
mask the errors that resolvers raise.

## More examples:

<details>
  <summary>Hide some exceptions</summary>

```python
import strawberry
from strawberry.extensions import MaskErrors
from graphql.error import GraphQLError


class VisibleError(Exception):
    pass


@strawberry.type
class Query:
    @strawberry.field
    def visible_error(self) -> str:
        raise VisibleError("This error will be visible")


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


@strawberry.type
class Query:
    @strawberry.field
    def hidden_error(self) -> str:
        raise KeyError("This error will not be visible")


schema = strawberry.Schema(
    Query,
    extensions=[
        MaskErrors(error_message="Oh no! An error occured. Very sorry about that."),
    ],
)
```

</details>

<details>
  <summary>Keep syntax and validation errors visible</summary>

By default, the extension also masks the errors that occur before execution. A
client that sends a malformed document thus gets only the generic message. Set
`mask_pre_execution_errors` to `False` to send these errors to the client. The
errors that resolvers raise stay masked.

```python
import strawberry
from strawberry.extensions import MaskErrors


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"

    @strawberry.field
    def hidden_error(self) -> str:
        raise KeyError("This error will not be visible")


schema = strawberry.Schema(
    Query,
    extensions=[
        lambda: MaskErrors(mask_pre_execution_errors=False),
    ],
)

# "Cannot query field 'helloo' on type 'Query'. Did you mean 'hello'?"
schema.execute_sync("{ helloo }")

# "Unexpected error."
schema.execute_sync("{ hiddenError }")
```

<Note>

Validation errors give the names of the fields, the arguments and the types of
your schema. They can also suggest a name that is close to the name that the
client sent. Disable this option only if the clients can know the shape of the
schema.

</Note>

</details>
