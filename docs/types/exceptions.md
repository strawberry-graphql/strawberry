---
title: Exceptions
toc: true
---

# Strawberry Exceptions

Strawberry raises some of its own exceptions.
Strawberry exception classes are defined in `strawberry.exceptions`.

## FieldWithResolverAndDefaultFactoryError

This exception is raised when in `strawberry.field` are specified both `resolver` and `default_factory`.

```python
@strawberry.type
class Query:
    @strawberry.field(default_factory=lambda: "Example C")
    def c(self) -> str:
        return "I'm a resolver"

// Throws 'Annotation for argument `argument` on field `name` cannot have multiple `strawberry.argument`s'

```

## FieldWithResolverAndDefaultValueError

This exception is raised when in `strawberry.field` are specified both `resolver` and `default`.

## InvalidFieldArgument

This exception is raised when a `Union` or `Interface` is used as an argument type.

## InvalidUnionType

This exception is raised when Scalar type

## MissingArgumentsAnnotationsError

The `MissingArgumentsAnnotationsError` exception is raised when the resolver's arguments are missing ot type-annotated.

> 'Missing annotation for arguments "foo" and "bar" in field "baz", did you forget to add it?'

## MissingFieldAnnotationError

The `MissingFieldAnnotationError` exception is raised when a `strawberry.field` is not type-annotated but also has no resolver to determine its type.

> 'Unable to determine the type of field "foo". Either annotate it directly, or provide a typed resolver using @strawberry.field.'

## MissingQueryError

This exception is raised when the request is missing the `query` paramater.

## MissingReturnAnnotationError

> 'Return annotation missing for field "goodbye", did you forget to add it?'

## MissingTypesForGenericError

## MultipleStrawberryArgumentsError

This exception is raised when `strawberry.argument` is used multiple times in a type annotation.

```python
import strawberry
from typing_extensions import Annotated


@strawberry.field
def name(
    argument: Annotated[
        str,
        strawberry.argument(description="This is a description"),
        strawberry.argument(description="Another description"),
    ]
) -> str:
    return "Name"

// Throws 'Annotation for argument `argument` on field `name` cannot have multiple `strawberry.argument`s'
```

## NotAnEnum

## PrivateStrawberryFieldError

## ScalarAlreadyRegisteredError

## UnallowedReturnTypeForUnion

## UnsupportedTypeError

## WrongNumberOfResultsReturned

## WrongReturnTypeForUnion
