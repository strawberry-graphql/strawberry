Release type: patch

Added a Flask view that allows you to query the schema and interact with it via GraphQL playground.

Usage:

```python
# app.py
from strawberry.flask.views import GraphQLView
from your_project.schema import schema

app = Flask(__name__)

app.add_url_rule(
    "/graphql", view_func=GraphQLView.as_view("graphql_view", schema=schema)
)

if __name__ == "__main__":
    app.run(debug=True)
```
