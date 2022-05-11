Release type: patch

This release adds a new flask view to allow for aysn dispatching of requests.

This is especially useful when using dataloaders with flask.

```python
from strawberry.flask.views import AsyncGraphQLView

...

app.add_url_rule("/graphql", view_func=AsyncGraphQLView.as_view("graphql_view", schema=schema, **kwargs))
```