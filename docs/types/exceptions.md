---
title: Exceptions
toc: true
---

# Strawberry Exceptions

Strawberry raises some of its own exceptions. Strawberry exception classes are defined in `strawberry.exceptions`.

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

```python
def test_resolver() -> str:
    return "I'm a resolver"

@strawberry.type
class Query:
    c: str = strawberry.field(default="Example C", resolver=test_resolver)

// Field "c" on type "Query" cannot define a default value and a resolver.
```

## InvalidFieldArgument

This exception is raised when a `Union` or `Interface` is used as an argument type.

## InvalidUnionType

This exception is raised when Scalar type

```python
@strawberry.type
class Noun:
    text: str

@strawberry.type
class Verb:
    text: str

Word = strawberry.union("Word", types=(Noun, Verb))

@strawberry.field
def add_word(word: Word) -> bool:
    return True

// Argument "word" on field "None" cannot be of type "Union"
```

## MissingArgumentsAnnotationsError

The `MissingArgumentsAnnotationsError` exception is raised when the resolver's arguments are missing ot type-annotated.

```python

@strawberry.field
def hello(self, foo) -> str:
    return "I'm a resolver"

// Missing annotation for argument "foo" in field "hello", did you forget to add it?
```

## MissingFieldAnnotationError

The `MissingFieldAnnotationError` exception is raised when a `strawberry.field` is not type-annotated but also has no resolver to determine its type.

```python
@strawberry.type
class Query:  # noqa: F841
    foo = dataclasses.field()

// Unable to determine the type of field "foo". Either annotate it directly, or provide a typed resolver using @strawberry.field.
```

## MissingQueryError

This exception is raised when the `request` is missing the `query` paramater.

## MissingReturnAnnotationError

The `MissingReturnAnnotationError` exception is raised when a resolver is missing the type annotation for the return type.

```python
@strawberry.type
class Query:
    @strawberry.field
    def goodbye(self):
        return "I'm a resolver"

// Return annotation missing for field "goodbye", did you forget to add it?
```

## MissingTypesForGenericError

This exception is raised when a generic types was used without passing any type.

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

## ObjectIsNotAClassError

This exception is raised when `strawberry.type`, `strawberry.input` or `strawberry.interface` are used with an object that is not class.

```python
@strawberry.type
def not_a_class():
    pass

// strawberry.type can only be used with class types. Provided object <function not_a_class at 0x10a20f700> is not a type.
```

## ObjectIsNotAnEnumError

This exception is raised when `strawberry.enum` is used with an object that is not an Enum

```python
@strawberry.enum
class NormalClass:
    hello = "world"

// strawberry.exceptions.NotAnEnum: strawberry.enum can only be used with subclasses of Enum
```

## PrivateStrawberryFieldError

This exception is raised when `strawberry.field` is type annotated Private.

```python
@strawberry.type
class Query:
    name: str
    age: strawberry.Private[int] = strawberry.field(description="🤫")


// Field age on type Query cannot be both private and a strawberry.field
```

## ScalarAlreadyRegisteredError

## UnallowedReturnTypeForUnion

## UnsupportedTypeError

## WrongNumberOfResultsReturned

## WrongReturnTypeForUnion
