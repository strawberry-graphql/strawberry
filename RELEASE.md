---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Instances of input types now work as
    argument and input field defaults, at execution and in introspection.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes argument and input field
    defaults that are instances of an input type, which failed when the field was
    executed and when the schema was queried with introspection.
---

This release fixes argument and input field defaults that are instances of an
input type:

```python
@strawberry.input
class Filter:
    limit: int = 10


@strawberry.type
class Query:
    @strawberry.field
    def items(self, filter: Filter = Filter(limit=5)) -> list[Item]: ...
```

Executing a field that used such a default failed with
`argument of type 'Filter' is not iterable`, and introspection queries failed
with `Invalid default value`. The same happened for input fields whose
`default_factory` returns an input instance.

Strawberry now converts these defaults to GraphQL input values when it builds
the schema, so introspection shows them, and resolvers get an instance built from
the default for every request, like when the client sends the value. Defaults
given as dicts keyed by Python names, like `{"page_size": 5}`, and `GlobalID`
defaults are converted too, instead of being ignored or failing when the field
is executed.

Printed and introspected defaults leave out `None` values that are the field's
default, and keep an explicit `null` only when it changes the value, for example
for a field whose default isn't `None`.
