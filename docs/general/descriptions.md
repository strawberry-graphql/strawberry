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
`description=` argument in strawberry decorators and annotations.

```python+schema
@strawberry.enum(description="Example enum")
class EnumType(Enum):
    FOO = strawberry.enum_value("foo", description="Some description")
    BAR = strawberry.enum_value("bar", description="Another description")


@strawberry.type(description="The main GraphQL type")
class Query:
    enum: EnumType = strawberry.field(
        default=EnumType.BAR, description="A dataclass field"
    )

    @strawberry.field(description="A GraphQL field with a resolver and arguments")
    def resolver(
        self,
        arg: Annotated[str, strawberry.argument(description="Argument description")],
    ) -> int:
        return 1


schema = strawberry.Schema(query=Query)
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
    """Argument description"""
    arg: String!
  ): Int!
}
```

## Formatting

[The GraphQL specification](https://spec.graphql.org/June2018/#sec-Descriptions)
requires all descriptions to be formatted using Markdown syntax (as specified by
[CommonMark](http://commonmark.org/))

## Docstrings

It is also possible to generate descriptions from Python docstrings.

Docstrings additionally allow specifying descriptions to class fields, enum values and resolver arguments when
one of the [supported syntaxes is used](https://pypi.org/project/docstring-parser/)

<Note>

The types of docstring used to produce GraphQL descriptions must be enabled globally with `StrawberryConfig(description_sources=[...])`, on the GraphQL type (e.g., `@strawberry.type(description_sources=[...]`) or on each member (e.g., `@strawberry.field(description_sources=[...])`), with the most specific (inner-most) option being used for each GraphQL element.

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


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(
        description_sources=DescriptionSources.RESOLVER_DOCSTRINGS
        | DescriptionSources.CLASS_DOCSTRINGS
    ),
)
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

## PEP 224 "Attribute Docstrings"

While [PEP 224](https://peps.python.org/pep-0224/) was rejected and attribute
docstrings are not recommended, specifying docstrings near each attributes
is sometimes preferrable.

Example:

```python+schema
@strawberry.enum
class EnumType(Enum):
    """Example enum"""

    FOO = "foo"
    """Some description"""

    BAR = "bar"
    """Another description"""


@strawberry.type
class Query:
    """The main GraphQL type"""

    enum: EnumType = EnumType.BAR
    """A dataclass field"""

    @strawberry.field
    def resolver(self, arg1: str, arg2: int) -> int:
        """
        A GraphQL field with a resolver and arguments

        Params:
            arg1: An enum argument
            arg2: An int argument
        """
        return 1


schema = strawberry.Schema(
    query=Query,
    config=StrawberryConfig(
        description_sources=DescriptionSources.RESOLVER_DOCSTRINGS
        | DescriptionSources.CLASS_DOCSTRINGS
        | DescriptionSources.ATTRIBUTE_DOCSTRINGS
    ),
)
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
