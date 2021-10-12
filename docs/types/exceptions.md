---
title: Exceptions
toc: true
---

# Strawberry Exceptions

Strawberry defines its library-specific exceptions in `strawberry.exceptions`.

## FieldWithResolverAndDefaultFactoryError

This exception is raised when `strawberry.field` is used with both
`resolver` and `default_factory` arguments.

```python
@strawberry.type
class Query:
    @strawberry.field(default_factory=lambda: "Example C")
    def c(self) -> str:
        return "I'm a resolver"

# Throws 'Field "c" on type "Query" cannot define a default_factory and a resolver.'

```

## FieldWithResolverAndDefaultValueError

This exception is raised when in `strawberry.field` is used with both
`resolver` and `default` arguments.

```python
def test_resolver() -> str:
    return "I'm a resolver"

@strawberry.type
class Query:
    c: str = strawberry.field(default="Example C", resolver=test_resolver)

# Throws 'Field "c" on type "Query" cannot define a default value and a resolver.'
```

## InvalidFieldArgument

This exception is raised when a `Union` or an `Interface` is used as an argument
type.

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

# Throws 'Argument "word" on field "None" cannot be of type "Union"'
```

## InvalidUnionType

This exception is raised when Scalar type is used with a `Union` or when the
list of types are not `strawberry.type`.

```python
@dataclass
class A:
    a: int

# Throws 'Union type `A` is not a Strawberry type'
```

## MissingArgumentsAnnotationsError

The `MissingArgumentsAnnotationsError` exception is raised when a resolver's
arguments are missing type annotations.

```python
@strawberry.field
def hello(self, foo) -> str:
    return "I'm a resolver"

# Throws 'Missing annotation for argument "foo" in field "hello", did you forget to add it?'
```

## MissingFieldAnnotationError

The `MissingFieldAnnotationError` exception is raised when a `strawberry.field`
is not type-annotated but also has no resolver to determine its type.

```python
@strawberry.type
class Query:  # noqa: F841
    foo = dataclasses.field()

# Throws 'Unable to determine the type of field "foo". Either annotate it directly, or provide a typed resolver using @strawberry.field.'
```

## MissingQueryError

This exception is raised when the `request` is missing the `query` paramater.

## MissingReturnAnnotationError

The `MissingReturnAnnotationError` exception is raised when a resolver is
missing the type annotation for the return type.

```python
@strawberry.type
class Query:
    @strawberry.field
    def goodbye(self):
        return "I'm a resolver"

# Throws 'Return annotation missing for field "goodbye", did you forget to add it?'
```

## MissingTypesForGenericError

This exception is raised when a generic types was used without passing any type.

## MultipleStrawberryArgumentsError

This exception is raised when `strawberry.argument` is used multiple times in a
type annotation.

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

# Throws 'Annotation for argument `argument` on field `name` cannot have multiple `strawberry.argument`s'
```

## ObjectIsNotAClassError

This exception is raised when `strawberry.type`, `strawberry.input` or
`strawberry.interface` are used with an object that is not class.

```python
@strawberry.type
def not_a_class():
    pass

# Throws 'strawberry.type can only be used with class types. Provided object <function not_a_class at 0x10a20f700> is not a type.'
```

## ObjectIsNotAnEnumError

This exception is raised when `strawberry.enum` is used with an object that is
not an Enum.

```python
@strawberry.enum
class NormalClass:
    hello = "world"

# Throws 'strawberry.exceptions.NotAnEnum: strawberry.enum can only be used with subclasses of Enum'
```

## PrivateStrawberryFieldError

This exception is raised when `strawberry.field` is type annotated with
`strawberry.Private`

```python
@strawberry.type
class Query:
    name: str
    age: strawberry.Private[int] = strawberry.field(description="🤫")


# Throws 'Field age on type Query cannot be both private and a strawberry.field'
```

## ScalarAlreadyRegisteredError

This exception is raised when two scalars are defined with the same name or the
same type. Note that also a `TypeError` will be thrown as well.

```python
MyCustomScalar = strawberry.scalar(
    str,
    name="MyCustomScalar",
)

MyCustomScalar2 = strawberry.scalar(
    int,
    name="MyCustomScalar",
)

@strawberry.type
class Query:
    scalar_1: MyCustomScalar
    scalar_2: MyCustomScalar2

# Throws 'Scalar `MyCustomScalar` has already been registered'
```

## UnallowedReturnTypeForUnion

This error is raised when the return type of a `Union` is not in the list of
Union types.

```python
@strawberry.type
class Outside:
    c: int

@strawberry.type
class A:
    a: int

@strawberry.type
class B:
    b: int

@strawberry.type
class Mutation:
    @strawberry.mutation
    def hello(self) -> Union[A, B]:
        return Outside(c=5)

query = """
    mutation {
        hello {
            __typename

            ... on A {
                a
            }

            ... on B {
                b
            }
        }
    }
"""

result = schema.execute_sync(query)
# result will look like:
# ExecutionResult(
#     data=None,
#     errors=[
#         GraphQLError(
#             "The type \"<class 'schema.Outside'>\" of the field \"hello\" is not in the list of the types of the union: \"['A', 'B']\"",
#             locations=[SourceLocation(line=3, column=9)],
#             path=["hello"],
#         )
#     ],
#     extensions={},
# )
```

## UnsupportedTypeError

This exception is thrown when the type-annotation used is not supported by
`strawberry.field` (yet).

## WrongNumberOfResultsReturned

This exception is thrown when the DataLoader returns a different number of
results than what we asked.

```python
async def idx(keys):
    return [1, 2]

loader = DataLoader(load_fn=idx)

await loader.load(1)

# Throws 'Received wrong number of results in dataloader, expected: 1, received: 2'
```

## WrongReturnTypeForUnion

This exception is thrown when the Union type cannot be resolved because it's not
a `strawberry.field`.
