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
of one more `"added"` than the previous one. Strawberry copies these lists again
when it converts the arguments, like it did before 0.275.5, which also covers
nested and optional lists, lists in input type defaults and directive arguments.
