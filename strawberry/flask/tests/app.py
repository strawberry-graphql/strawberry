from flask import Flask
from strawberry.flask.views import GraphQLView

from .schema import schema


def init_app(path="/graphql", **kwargs):
    app = Flask(__name__)
    app.debug = True
    app.add_url_rule(
        "/graphql", view_func=GraphQLView.as_view("graphql_view", schema=schema)
    )
    return app


if __name__ == "__main__":
    app = init_app()
    app.run()
