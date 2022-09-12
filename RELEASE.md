Release type: minor

Convert Tuple and Sequence types to GraphQL list types.

Example:

```python
from collections.abc import Sequence
from typing import Tuple

@strawberry.type
class User:
    pets: Sequence[Pet]
    favourite_ice_cream_flavours: Tuple[IceCreamFlavour]
```
