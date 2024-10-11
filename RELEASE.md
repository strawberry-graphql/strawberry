Release type: patch

Use native enum `__doc__` as the description for the schema enum type.

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
