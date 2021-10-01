Release type: patch

This release add support for the upcoming python 3.10 and it adds support
for the new union syntax, allowing to declare unions like this:

```python
import strawberry

@strawberry.type
class User:
    name: str

@strawberry.type
class Error:
    code: str

@strawberry.type
class Query:
    find_user: User | Error
```
