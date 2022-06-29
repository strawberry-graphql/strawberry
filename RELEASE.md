Release type: minor

This release changes how we declare the `info` argument in resolvers and the
`value` argument in directives.

Previously we'd use the name of the argument to determine its value. Now we use
the type annotation of the argument to determine its value.

Here's an example of how the old syntax works:

```python
def some_resolver(info) -> str:
    return info.context.get("some_key", "default")

@strawberry.type
class Example:
    a_field: str = strawberry.resolver(some_resolver)
```

and here's an example of how the new syntax works:

```python
from strawberry.types import Info

def some_resolver(info: Info) -> str:
    return info.context.get("some_key", "default")

@strawberry.type
class Example:
    a_field: str = strawberry.resolver(some_resolver)
```

This means that you can now use a different name for the `info` argument in your
resolver and the `value` argument in your directive.

Here's an example that uses a custom name for both the value and the info
parameter in directives:

```python
from strawberry.types import Info
from strawberry.directive import DirectiveLocation, DirectiveValue

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

**Note:** the old way of passing arguments by name is deprecated and will be
removed in future releases of Strawberry.
