---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release ensures `MaskErrors` also
    masks parsing and validation errors during synchronous execution. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes `MaskErrors` so
    synchronous parsing and validation failures no longer expose their original
    error details.
---

This release fixes an issue where `MaskErrors` leaked parsing and validation
error details during synchronous execution.

Synchronous execution now masks pre-execution errors consistently with
asynchronous execution, including when `ValidationCache` is enabled.
