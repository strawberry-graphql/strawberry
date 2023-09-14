Release type: minor

Adds new strawberry.Parent type annotation to support resolvers without use of self.

E.g.

```python
@dataclass
class UserRow:
    id_: str


@strawberry.type
class User:
    @strawberry.field
    @staticmethod
    async def name(parent: strawberry.Parent[UserRow]) -> str:
        return f"User Number {parent.id}"


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return UserRow(id_="1234")
```
