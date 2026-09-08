---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Annotate the `None` member of a union in
    your Pydantic model, like `Union[str, SkipJsonSchema[None]]`, and your
    schema builds instead of raising InvalidUnionTypeError. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. If you annotate the `None` member of a
    union in a Pydantic model, for example `Union[str, SkipJsonSchema[None]]`,
    Strawberry now reads that field as an optional field and builds your schema
    instead of raising InvalidUnionTypeError.
---

This release fixes Pydantic fields that annotate the `None` member of a union.

Write `field_a: Union[str, SkipJsonSchema[None]]` in your model and Strawberry
now gives you a nullable `String`. Before, the `Annotated` wrapper hid the
`NoneType` that marks a field optional, so Strawberry read the field as a real
GraphQL union and raised `InvalidUnionTypeError`, telling you that `str` cannot
be used in a GraphQL union. Strawberry unwraps that `None` member now, and
leaves the metadata on every other member alone, so `strawberry.lazy` references and
`strawberry.union` names keep working.
