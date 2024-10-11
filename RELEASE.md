Release type: patch

Use native enum `__doc__` as the description for the schema enum type.

This change improves consistency between Python enums and schema representations,
and leverages existing documentation for better maintainability and clarity.

```py
# somewhere.py
from enum import Enum


class AnimalKind(Enum):
    """The kind of animal."""

    AXOLOTL, CAPYBARA = range(2)
```

This will generate the following schema:

```graphql
"""The kind of animal."""
enum AnimalKind {
  AXOLOTL
  CAPYBARA
}
```
