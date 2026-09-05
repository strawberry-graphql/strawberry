Release type: minor

This release changes the Python query codegen plugin to generate `TypedDict` classes instead of plain classes. This provides better type safety for dictionary-like access patterns commonly used when working with JSON responses from GraphQL APIs.

**Before:**

```python
class MyQueryResult:
    user: str
```

**After:**

```python
from typing_extensions import TypedDict


class MyQueryResult(TypedDict):
    user: str
```

Optional fields with default values now use `NotRequired` instead of the `= value` syntax (which TypedDict doesn't support):

```python
class PersonInput(TypedDict):
    name: str
    age: NotRequired[Optional[int]]  # was: age: Optional[int] = None
```
