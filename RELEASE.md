Release type: patch

This release adds support for using rwa Python enum types in your schema 
(enums that are not decorated with `@strawberry.enum`)

This is useful if you have enum types from other places in your code
that you want to use in strawberry.
i.e
```py
# somewhere.py
from enum import Enum

class AnimalKind(Enum):
    AXOLOTL, CAPYBARA = range(2)

# gql/animals
from somewhere import AnimalKind


@strawberry.type
class AnimalType:
    kind: AnimalKind
```