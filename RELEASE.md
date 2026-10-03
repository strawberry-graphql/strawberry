---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Integrations can now choose which fields of
    an input instance make an argument or input field default, with a new
    to_input hook. https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds a to_input hook to
    Strawberry's type definitions, the counterpart of from_input, so integrations
    can choose which fields of an input instance are used when it's an argument
    or input field default.
---

This release adds a `to_input` hook to `StrawberryObjectDefinition`, the
counterpart of `from_input`. Like `from_input`, it's meant for integrations that
create their own type definitions, which pass it when they create the
definition. It isn't meant to be set on types defined with `@strawberry.input`.

Strawberry converts input instances used as argument and input field defaults to
GraphQL input values when it builds the schema. When the input type sets
`to_input`, Strawberry calls it to get the instance's fields, instead of using
all of them. For example, an integration for Pydantic models can use it to only
include the fields that were set, so that the default of
`patch: UserPatch = UserPatch(name="Ada")` is `{ name: "Ada" }`, instead of
setting every other field to `None`:

```python
from typing import Any

from pydantic import BaseModel

from strawberry.types.base import StrawberryObjectDefinition


def dump_model(model: BaseModel) -> dict[str, Any]:
    return {name: getattr(model, name) for name in model.model_fields_set}


definition = StrawberryObjectDefinition(
    name="UserPatch",
    is_input=True,
    # the other arguments of the definition
    to_input=dump_model,
)
```

The hook returns the values of the fields, keyed by their Python names. Every
field it returns is part of the default, with `None` as an explicit null, unless
its value is `UNSET`, and nested input instances use their own type's
`to_input`. The fields it leaves out aren't part of the default.
