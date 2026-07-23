---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Pydantic fields now keep their NewType
    scalar mappings when Strawberry builds the GraphQL schema. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Pydantic fields annotated with NewType now
    respect StrawberryConfig scalar mappings during schema generation, keeping
    the generated GraphQL scalar consistent with runtime conversion.
---

This release fixes `StrawberryConfig.scalar_map` being ignored for Pydantic
fields annotated with `NewType`.

Strawberry now preserves the annotation until schema scalar resolution, so the
generated GraphQL type and runtime scalar conversion use the same configured
scalar. Unmapped `NewType` annotations continue to resolve through their
underlying type.
