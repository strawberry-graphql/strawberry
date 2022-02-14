Release type: minor

Support using docstrings are GraphQL descriptions

It is now possible to use python docstrings to provide GraphQL descriptions.

## Example

Here is an example of using docstrings in types and fields:

```
def external_resolver() -> int:
    """ External resolver with docstring"""
    return 2

@strawberry.type
class Query:
    """
    Main entrypoint to GraphQL data

    It can now be documented with docstrings
"""

    x: int = strawberry.field(default=1, description="Dataclass field")
    y: int = strawberry.field(resolver=external_resolver)

    @strawberry.field
    def z(self) -> int:
        """ Method resolver with docstring """
        return 3
```

It produces this GraphQL schema:

```
"""
Main entrypoint to GraphQL data

It can now be documented with docstrings
"""
type Query {
  """Dataclass field"""
  x: Int!

  """External resolver with docstring"""
  y: Int!

  """Method resolver with docstring """
  z: Int!
}

```
