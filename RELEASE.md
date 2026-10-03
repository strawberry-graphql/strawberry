---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes list defaults being
    shared between requests, so a resolver that changes a default list no longer
    changes it for the next requests. https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes list defaults of
    arguments and input fields being shared between requests: each request now
    gets its own copy, so a resolver that changes a default list no longer
    changes it for the following requests or in the printed schema.
---

This release fixes list defaults of arguments and input fields being shared
between requests.

When a client omitted an argument or input field whose default is a list of
scalars or enums, every request got the same list. A resolver that changed it,
for example by appending to it, changed the default for all the following
requests, and the default printed in the schema too:

```python
import strawberry


@strawberry.input
class Filter:
    tags: list[str] = strawberry.field(default_factory=lambda: ["base"])


@strawberry.type
class Query:
    @strawberry.field
    def search(self, filter: Filter) -> list[str]:
        filter.tags.append("added")

        return filter.tags
```

Each `{ search(filter: {}) }` request now returns `["base", "added"]`, instead
of one more `"added"` than the previous one. This also applies to nested and
optional lists, lists in input type defaults and directive arguments.

Strawberry now keeps list defaults as tuples, which can't be changed, and gives
each request its own list when it converts the arguments. Lists sent by clients
are still used as they are, without copying them. Code that reads the defaults
before Strawberry converts them, like `info.variable_values` or a `from_input`
hook, gets them as tuples.
