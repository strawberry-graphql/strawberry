import strawberry
from strawberry.extensions import Extension


class MyExtension(Extension):
    def get_results(self):
        return {"example": "example"}


@strawberry.type
class Query:
    hello: str = "🍓"


schema = strawberry.Schema(query=Query, extensions=[MyExtension])
