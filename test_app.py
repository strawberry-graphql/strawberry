import strawberry
from flask import Flask
from flask_api.views import GraphQLView


@strawberry.type
class User:
    name: str
    age: int


@strawberry.type
class Query:
    @strawberry.field
    def user(self, info) -> User:
        return User(name="Patrick", age=100)


schema = strawberry.Schema(query=Query)

app = Flask(__name__)

app.add_url_rule(
    "/graphql", view_func=GraphQLView.as_view("graphql_view", schema=schema)
)


if __name__ == "__main__":
    app.run(debug=True)
