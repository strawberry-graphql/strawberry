---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Integrations can now control how input
    types are built from GraphQL input values, with a new from_input hook.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds a from_input hook to
    Strawberry's type definitions, so integrations can build input values their
    own way, for example to validate them, with access to the request info and
    the location of the value in the arguments.
---

This release adds a `from_input` hook to `StrawberryObjectDefinition`, so input
types can build their own value from a GraphQL input value.

When a type definition sets `from_input`, Strawberry calls it with the class to
build, the input value keyed by GraphQL field names, and an `InputContext`,
instead of converting the fields and passing them to the class:

```python
from collections.abc import Mapping
from typing import Any

import strawberry
from strawberry.types.arguments import InputContext
from strawberry.types.base import get_object_definition


@strawberry.input
class Range:
    start: int
    end: int


def build_range(cls: type, value: Mapping[str, Any], context: InputContext) -> Any:
    if value["start"] > value["end"]:
        location = ".".join(map(str, context.path))

        raise ValueError(f"{location}: start must be before end")

    return cls(start=value["start"], end=value["end"])


get_object_definition(Range, strict=True).from_input = build_range
```

`InputContext` has the request's `info`, the schema config and scalar registry,
the `path` of the value in the arguments, made of GraphQL field names and list
indices, like `("input", "items", 0)`, and a `convert()` method that converts
nested values like Strawberry does. The hook is used for field arguments,
directive arguments and federation entities, and for argument and input field
defaults, which Strawberry converts to input values when it builds the schema.
