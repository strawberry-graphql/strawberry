Release type: patch

In this release, we updated Strawberry to gracefully handle requests containing
an invalid `variables` parameter. Previously, such requests could result in
internal server errors. Now, Strawberry will return a 400 Bad Request response
with a clear error message, conforming to the GraphQL over HTTP specification.
