Release type: minor

Support using docstrings as GraphQL descriptions

It is now possible to use python docstrings to provide GraphQL descriptions.

## Example

Here is an example of using docstrings in types and fields:

```python
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
    def resolver(self, arg1: enum, arg2: int) -> int:
        """
        A GraphQL field with a resolver and arguments

        Params:
            arg1: An enum argument
            arg2: An int argument
        """
        return 1
```

Produces this GraphQL schema:

```graphql
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
    arg1: EnumType!

    """An int argument"""
    arg2: Int!
  ): Int!
}
```
