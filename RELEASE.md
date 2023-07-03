Release type: patch

Enhancements:
- Improved pydantic conversion compatibility with specialized list classes.
  - Modified `StrawberryAnnotation._is_list` to check if the `annotation` extends from the `list` type, enabling it to be considered a list.
  - in `StrawberryAnnotation` Moved the `_is_list` check before the `_is_generic` check in `resolve` to avoid `unsupported` error in `_is_generic` before it checked `_is_list`.

This enhancement enables the usage of constrained lists as class types and allows the creation of specialized lists. The following example demonstrates this feature:

```python
import strawberry
from pydantic import BaseModel, ConstrainedList


class FriendList(ConstrainedList):
    min_items = 1


class UserModel(BaseModel):
    age: int
    friend_names: FriendList[str]


@strawberry.experimental.pydantic.type(UserModel)
class User:
    age: strawberry.auto
    friend_names: strawberry.auto
```
