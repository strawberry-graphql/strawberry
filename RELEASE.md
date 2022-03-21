Release type: minor

This release Closes [#1666] by improving the injection of reserved arguments
for resolvers and directives through use of an annotation-based approach which
adds support for:

1. Defining a directive value argument using a `DirectiveValue`
annotation.
2. Defining the resolve/directive `info` argument using the `Info` annotation

**Deprecated:** Declaration of value and info arguments by relying on name-based
matching without annotations.

# Examples

```python
@strawberry.type
class Cake:
    frosting: Optional[str] = None
    flavor: str = "Chocolate"

@strawberry.type
class Query:
    @strawberry.field
    def cake(self) -> Cake:
        return Cake()

@strawberry.directive(
    locations=[DirectiveLocation.FIELD],
    description="Add frosting with ``value`` to a cake.",
)
def add_frosting(value: str, v: DirectiveValue[Cake], my_info: Info):
    # Arbitrary argument name when using `DirectiveValue` is supported!
    assert isinstance(v, Cake)
    if value in my_info.context["allergies"]:  # Info can now be accessed from directives!
        raise AllergyError("You are allergic to this frosting!")
    else:
        v.frosting = value  # Value can now be used as a GraphQL argument name!
    return v
```

[#1666]: (https://github.com/strawberry-graphql/strawberry/issues/1666)
