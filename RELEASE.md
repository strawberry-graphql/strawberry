Release type: minor

This release improves support for django and asgi integration.

It allows to use async resolvers when using django. It also changes the status
code from 400 to 200 even if there are errors this makes it possible to still
use other fields even if one raised an error.

We also moved strawberry.contrib.django to strawberry.django, so if you're using
the django view make sure you update the paths.
