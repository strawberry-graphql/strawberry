Release type: minor

This release adds support for passing `json_encoder` and `json_dumps_params` to Sanic's view.


```python
from strawberry.sanic.views import GraphQLView

from api.schema import Schema

app = Sanic(__name__)

app.add_route(
    GraphQLView.as_view(
        schema=schema,
        graphiql=True,
        json_encoder=CustomEncoder,
        json_dumps_params={},
    ),
    "/graphql",
)
```
