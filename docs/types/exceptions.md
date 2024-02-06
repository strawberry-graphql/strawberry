---
title: Exceptions
toc: true
---

# Strawberry Exceptions

Strawberry defines its library-specific exceptions in `strawberry.exceptions`.

## Strawberry Schema Exceptions

### FieldWithResolverAndDefaultFactoryError

This exception is raised when `strawberry.field` is used with both `resolver`
and `default_factory` arguments.

```python
@strawberry.type
class Query:
    @strawberry.field(default_factory=lambda: "Example C")
    def c(self) -> str:
        return "I'm a resolver"


# Throws 'Field "c" on type "Query" cannot define a default_factory and a resolver.'
```

### FieldWithResolverAndDefaultValueError

This exception is raised when `strawberry.field` is used with both `resolver`
and `default` arguments.

```python
def test_resolver() -> str:
    return "I'm a resolver"


@strawberry.type
class Query:
    c: str = strawberry.field(default="Example C", resolver=test_resolver)


# Throws 'Field "c" on type "Query" cannot define a default value and a resolver.'
```

### MissingTypesForGenericError

This exception is raised when a `Generic` type is added to the Strawberry Schema
without passing any type to make it concrete.

### MultipleStrawberryArgumentsError

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

### UnsupportedTypeError

This exception is thrown when the type-annotation used is not supported by
`strawberry.field`. At the time of writing this exception is used by Pydantic
only

```python
class Model(pydantic.BaseModel):
    field: pydantic.Json


@strawberry.experimental.pydantic.type(Model, fields=["field"])
class Type:
    pass
```

### WrongNumberOfResultsReturned

This exception is raised when the DataLoader returns a different number of
results than requested.

```python
async def idx(keys):
    return [1, 2]


loader = DataLoader(load_fn=idx)

await loader.load(1)

# Throws 'Received wrong number of results in dataloader, expected: 1, received: 2'
```

## Runtime exceptions

Some errors are also thrown when trying to exectuing queries (mutations or
subscriptions).

### MissingQueryError

This exception is raised when the `request` is missing the `query` parameter.

```python
client.post("/graphql", data={})

# Throws 'Request data is missing a "query" value'
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

## WrongReturnTypeForUnion

This exception is thrown when the Union type cannot be resolved because it's not
a `strawberry.field`.

```python
@strawberry.type
class A:
    a: int


@strawberry.type
class B:
    b: int


@strawberry.type
class Query:
    ab: Union[A, B] = "ciao"  # missing `strawberry.field` !


query = """{
    ab {
        __typename,

        ... on A {
            a
        }
    }
}"""

result = schema.execute_sync(query, root_value=Query())

# result will look like:
# ExecutionResult(
#     data=None,
#     errors=[
#         GraphQLError(
#             'The type "<class \'str\'>" cannot be resolved for the field "ab" , are you using a strawberry.field?',
#             locations=[SourceLocation(line=2, column=9)],
#             path=["ab"],
#         )
#     ],
#     extensions={},
# )
```
