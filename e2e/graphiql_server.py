"""Simple Strawberry server for GraphiQL e2e testing."""  # noqa: INP001

import strawberry
from strawberry.asgi import GraphQL


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, name: str = "World") -> str:
        return f"Hello, {name}!"

    @strawberry.field
    def add(self, a: int, b: int) -> int:
        return a + b


schema = strawberry.Schema(query=Query)
app = GraphQL(schema)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
