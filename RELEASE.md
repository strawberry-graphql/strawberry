Release type: patch

This release adds support for using strawberry.enum as a function with MyPy,
this is now valid typed code:

```python
from enum import Enum

import strawberry

class IceCreamFlavour(Enum):
    VANILLA = "vanilla"
    STRAWBERRY = "strawberry"
    CHOCOLATE = "chocolate"

Flavour = strawberry.enum(IceCreamFlavour)
```
