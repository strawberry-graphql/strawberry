Release type: minor

Support using docstrings as GraphQL descriptions

It is now possible to use python docstrings to provide GraphQL descriptions.

## Example

Here is an example of using docstrings in types and fields:

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
