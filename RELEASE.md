Release type: minor

Add full support for forward references, specially when using
`from __future__ import annotations`.

Before the following would fail on python versions older than 3.10:

```python
from __future__ import annotations

import strawberry


@strawberry.type
class Query:
    foo: str | None
```

Also, this would fail in any python versions:

```python
from __future__ import annotations

from typing import Annotated

import strawberry


@strawberry.type
class Query:
    foo: Annotated[str, "some annotation"]
```

Now both of these cases are supported.
Please open an issue if you find any edge cases that are still not supported.
