---
title: Descriptions
---

# Descriptions

Documentation is first‐class feature of GraphQL, and human-readable
descriptions can be added into all GraphQL types, fields and
other definitions.

These are often shown by interactive GraphQL clients (Like
[GraphiQL](https://github.com/graphql/graphiql) and documentation generators.

The preferred way of adding description in strawberry is using the
`description=` argument in strawberry decorators:

```python+schema
    @strawberry.enum(description="Example enum")
    class EnumType(Enum):
        FOO = "foo"
        BAR = "bar"

    @strawberry.type(description="The main GraphQL type")
    class Query:
        enum: EnumType = strawberry.field(default=EnumType.BAR, description="A dataclass field")

        @strawberry.field(description="A GraphQL field with a resolver and arguments")
        def resolver(self, arg1: str, arg2: int) -> int:
            return 1

    schema = strawberry.Schema(query=Query)
---
"""Example enum"""
enum EnumType {
  FOO
  BAR
}

"""The main GraphQL type"""
type Query {
  """A dataclass field"""
  enum: EnumType!

  """A GraphQL field with a resolver and arguments"""
  resolver(arg1: String!, arg2: Int!): Int!
}
```

## Formatting

Descriptions should be formatted using Markdown syntax (as specified by
[CommonMark](http://commonmark.org/))

## Docstrings

It is also possible to generate descriptions from Python docstrings.

Additionally it is possible to add descriptions to enum values and resolver arguments when
one of the [supported syntaxes is used](https://pypi.org/project/docstring-parser/)

<Note>

This needs to be explicitly enabled with `StrawberryConfig(description_from_docstrings=True)`

</Note>

Example:

```python+schema
@strawberry.enum
class EnumType(Enum):
    """
    Example enum

    Attributes:
        FOO: Some description
        BAR: Another description
    """

    FOO = "foo"
    BAR = "bar"

@strawberry.type
class Query:
    """
    The main GraphQL type

    Attributes:
        enum: A dataclass field
    """
    enum: EnumType = EnumType.BAR

    @strawberry.field
    def resolver(self, arg1: str, arg2: int) -> int:
        """
        A GraphQL field with a resolver and arguments

        Params:
            arg1: An enum argument
            arg2: An int argument
        """
        return 1

schema = strawberry.Schema(query=Query, config=StrawberryConfig(description_from_docstrings=True))
---
"""Example enum"""
enum EnumType {
  """Some description"""
  FOO

  """Another description"""
  BAR
}

"""The main GraphQL type"""
type Query {
  """A dataclass field"""
  enum: EnumType!

  """A GraphQL field with a resolver and arguments"""
  resolver(
    """An enum argument"""
    arg1: String!

    """An int argument"""
    arg2: Int!
  ): Int!
}
```
