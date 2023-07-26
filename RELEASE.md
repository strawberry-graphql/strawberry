Release type: minor

This release adds support for union with a single member, they are
useful for future proofing your schema in cases you know a field
will be part of a union in future.

```python
import strawberry

from typing import Annotated


@strawberry.type
class Audio:
    duration: int


@strawberry.type
class Query:
    # note: Python's Union type doesn't support single members,
    # Union[Audio] is exactly the same as Audio, so we use
    # use Annotated and strawberry.union to tell Strawberry this is
    # a union with a single member
    latest_media: Annotated[Audio, strawberry.union("MediaItem")]


schema = strawberry.Schema(query=Query)
```
