Release type: minor

This release adds support for enabling subscriptions in GraphiQL
on Django by setting a flag `subscriptions_enabled` on the BaseView class.
```python
from strawberry.django.views import AsyncGraphQLView

from .schema import schema

urlpatterns = [path("graphql", AsyncGraphQLView.as_view(schema=schema, graphiql=True, subscriptions_enabled=True))]
```
