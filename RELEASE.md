Release type: patch

This release fixes an issue where optional lazy types using `| None` were
failing to be correctly resolved inside modules using future annotations, e.g.

```python
from __future__ import annotations

from typing import Annotated, TYPE_CHECKING

import strawberry

if TYPE_CHECKING:
    from types import Group


@strawberry.type
class Person:
    group: Annotated["Group", strawberry.lazy("types.group")] | None
```

This should now work as expected.
