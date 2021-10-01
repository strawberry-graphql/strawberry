import strawberry
from strawberry.extensions import Extension


class MyExtension(Extension):
    def get_results(self):
        return {"example": "example"}


@strawberry.type
class Query:
    hello: str = "🍓"

    @strawberry.field
    def hi(self, name: str) -> str:
        return f"Hi {name}!"


schema = strawberry.Schema(query=Query, extensions=[MyExtension])
