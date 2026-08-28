---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes Annotated field
    configuration with postponed annotations, defaults, and combined metadata.
    🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes Annotated field
    configuration with postponed annotations, dataclass defaults, and combined
    Strawberry metadata.
---

This release fixes fields configured with `strawberry.field()` inside
`typing.Annotated`.

Field options now work with postponed annotations, `default` and
`default_factory` configure the generated dataclass constructor, and other
Annotated metadata such as named unions is preserved.
