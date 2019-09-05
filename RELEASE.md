Release type: patch

Added a Django view that allows you to query the schema and interact with it via GraphQL playground.

Usage:

```python

# Install
$ pip install strawberry-graphql[django]

# settings.py
INSTALLED_APPS = [
    ...
    'strawberry.contrib.django',
]

# urls.py
from strawberry.contrib.django.views import GraphQLView
from your_project.schema import schema

urlpatterns = [
    path('graphql/', GraphQLView.as_view(schema=schema)),
]

```