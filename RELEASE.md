Release type: patch

In this release, we updated Strawberry to gracefully handle requests containing
an invalid `query` parameter. Previously, such requests could result in internal
server errors, but now they will return a 400 Bad Request response with an
appropriate error message, conforming to the GraphQL over HTTP specification.
