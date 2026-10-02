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

This release adds a `from_input` hook to `StrawberryObjectDefinition`, for
integrations that create their own type definitions, like the first-class
Pydantic integration. It lets them build input values their own way, for example
to validate a whole input with the request's info. It isn't meant to be set on
types defined with `@strawberry.input`.

An integration passes the hook when it creates the type definition. Strawberry
then calls it with the class to build, the input value keyed by GraphQL field
names, and an `InputContext`, instead of converting the fields and passing them
to the class:

```python
from collections.abc import Mapping
from typing import Any

from strawberry.types.arguments import InputContext
from strawberry.types.base import StrawberryObjectDefinition


def build_model(cls: type, value: Mapping[str, Any], context: InputContext) -> Any:
    return cls.model_validate(value, context={"info": context.info})


definition = StrawberryObjectDefinition(
    name="UserInput",
    is_input=True,
    # the other arguments of the definition
    from_input=build_model,
)
```

`InputContext` has the request's `info`, the schema config and scalar registry,
the `path` of the value in the arguments, made of GraphQL field names and list
indices, like `("input", "items", 0)`, and a `convert()` method that converts
nested values like Strawberry does, given a Strawberry type or an annotation
like `list[Item]`. Its keys are the location of the value in the input, so inputs
nested in it know their own location:

```python
context.convert(value["items"][0], Item, "items", 0)
```

The hook is used for field arguments, directive arguments and federation
entities, and for argument and input field defaults, which Strawberry converts
to input values when it builds the schema. Federation entities have the location
of their representation, like `("representations", 0)`, and GraphQL errors
raised while building them are now returned to the client, instead of a generic
"Unable to resolve reference" error.
