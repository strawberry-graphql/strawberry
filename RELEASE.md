Release type: patch

This release adds support for passing `json_encoder` and `json_dumps_params` to Django [`JsonResponse`](https://docs.djangoproject.com/en/stable/ref/request-response/#jsonresponse-objects) via a view.


```python
from json import JSONEncoder

from django.urls import path
from strawberry.django.views import AsyncGraphQLView

from .schema import schema

# Pass the JSON params to `.as_view`
urlpatterns = [
    path(
        "graphql",
        AsyncGraphQLView.as_view(
            schema=schema,
            json_encoder=JSONEncoder,
            json_dumps_params={"separators": (",", ":")},
        ),
    ),
]

# … or set them in a custom view
class CustomAsyncGraphQLView(AsyncGraphQLView):
    json_encoder = JSONEncoder
    json_dumps_params = {"separators": (",", ":")}
```
