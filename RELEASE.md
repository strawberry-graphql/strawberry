Release type: minor

This release adds support for list arguments in operation directives.

The following is now supported:

```python
@strawberry.directive(locations=[DirectiveLocation.FIELD])
def append_names(
    value: DirectiveValue[str], names: List[str]
):  # note the usage of List here
    return f"{value} {', '.join(names)}"
```
