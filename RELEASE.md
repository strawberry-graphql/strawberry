Release type: minor

This release adds a new `MaskErrors` extension that can be used to hide error
messages from the client to prevent exposing sensitive details.

```python
import strawberry
from strawberry.extensions import MaskErrors

schema = strawberry.Schema(
    Query,
    extensions=[
        MaskErrors(visible_errors=[MyVisibleError]),
    ]
)
```
