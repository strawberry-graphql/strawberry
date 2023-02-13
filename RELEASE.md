Release type: patch

This release fixes a regression introduce in version 0.156.2 that
would make Mypy throw an error in the following code:

```python
import strawberry


@strawberry.type
class Author:
    name: str


@strawberry.type
class Query:
    @strawberry.field
    async def get_authors(self) -> list[Author]:
        return [Author(name="Michael Crichton")]
```
