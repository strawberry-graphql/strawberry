Release type: patch

This release fixes an issue with optional scalars using the `or`
notation with forward references on python 3.10.

The following code would previously raise `TypeError` on python 3.10:

```python
from __future__ import annotations

import strawberry
from strawberry.scalars import JSON


@strawberry.type
class SomeType:
    an_optional_json: JSON | None
```
