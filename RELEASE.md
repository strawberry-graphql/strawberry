---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes dataclass transform
    metadata so custom ordering methods are correctly accepted by type checkers. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes dataclass transform
    metadata so custom ordering methods are correctly accepted by type checkers.
---

This release fixes incorrect dataclass transform ordering metadata.

Strawberry decorators now correctly declare that ordering methods are not generated
by default, matching their runtime dataclass behavior and allowing custom ordering
methods such as `__gt__` to be used without type-checking errors.
