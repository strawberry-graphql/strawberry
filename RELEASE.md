---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release makes built-in scalar and
    OneOf input errors classifiable without changing GraphQL responses.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release makes built-in scalar and
    OneOf input errors classifiable for more accurate error monitoring without
    changing GraphQL responses.
---

This release fixes classification of built-in scalar and OneOf input errors.

Strawberry now raises `StrawberryInputCoercionError` for these client input
errors, allowing server-side error handling and monitoring to distinguish them
from server faults without changing error messages or serialized responses.
Custom scalar parsers can raise the same exception for expected conversion
errors.
