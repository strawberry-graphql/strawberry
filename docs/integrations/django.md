---
title: Django
---

# Django

Strawberry comes with a basic [Django integration](https://github.com/strawberry-graphql/strawberry-graphql-django).
It provides a view that you can use to serve your GraphQL schema:

```python
from django.urls import path

from strawberry.django.views import GraphQLView

from api.schema import schema

urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema)),
]
```

You'd also need to add `strawberry.django` to the `INSTALLED_APPS` of your
project, this is needed to provide the template for the GraphiQL interface.

## Options

The `GraphQLView` accepts two options at the moment:

- schema: mandatory, the schema created by `strawberry.Schema`.
- graphiql: optional, defaults to `True`, whether to enable the GraphiQL
  interface.

## Extending the view

We allow to extend the base `GraphQLView`, by overriding the following methods:

- `get_context(self, request: HttpRequest) -> Any`
- `get_root_value(self, request: HttpRequest) -> Any`
- `process_result(self, request: HttpRequest, result: ExecutionResult) -> GraphQLHTTPResponse`

## get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a
`StrawberryDjangoContext` object.

```python
@strawberry.type
class Query:
    @strawberry.field
    def user(self, info: Info) -> str:
        return str(info.context.request.user)
```

or in case of a custom context:

```python
class MyGraphQLView(GraphQLView):
    def get_context(self, request: HttpRequest, response: HttpResponse) -> Any:
        return {"example": 1}


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: Info) -> str:
        return str(info.context["example"])
```

Here we are returning a custom context dictionary that contains only one item
called "example".

Then we use the context in a resolver, the resolver will return "1" in this
case.

## get_root_value

`get_root_value` allows to provide a custom root value for your schema, this is
probably not used a lot but it might be useful in certain situations.

Here's an example:

```python
class MyGraphQLView(GraphQLView):
    def get_root_value(self, request: HttpRequest) -> Any:
        return Query(name="Patrick")


@strawberry.type
class Query:
    name: str
```

Here we are returning a Query where the name is "Patrick", so we when requesting
the field name we'll return "Patrick" in this case.

## process_result

`process_result` allows to customize and/or process results before they are sent
to the clients. This can be useful logging errors or hiding them (for example to
hide internal exceptions).

It needs to return an object of `GraphQLHTTPResponse` and accepts the request
and the execution results.

```python
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from graphql.error import format_error as format_graphql_error

class MyGraphQLView(GraphQLView):
    def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [format_graphql_error(err) for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

# Async Django

Strawberry also provides an async view that you can use with Django 3.1+

```python
from django.urls import path

from strawberry.django.views import AsyncGraphQLView

from api.schema import schema

urlpatterns = [
    path("graphql/", AsyncGraphQLView.as_view(schema=schema)),
]
```

You'd also need to add `strawberry.django` to the `INSTALLED_APPS` of your
project, this is needed to provide the template for the GraphiQL interface.

## Options

The `AsyncGraphQLView` accepts two options at the moment:

- schema: mandatory, the schema created by `strawberry.Schema`.
- graphiql: optional, defaults to `True`, whether to enable the GraphiQL
  interface.

## Extending the view

We allow to extend the base `AsyncGraphQLView`, by overriding the following
methods:

- `async get_context(self, request: HttpRequest) -> Any`
- `async get_root_value(self, request: HttpRequest) -> Any`
- `async process_result(self, request: HttpRequest, result: ExecutionResult) -> GraphQLHTTPResponse`

## get_context

`get_context` allows to provide a custom context object that can be used in your
resolver. You can return anything here, by default we return a dictionary with
the request.

```python
class MyGraphQLView(AsyncGraphQLView):
    async def get_context(self, request: HttpRequest, response: HttpResponse) -> Any:
        return {"example": 1}


@strawberry.type
class Query:
    @strawberry.field
    def example(self, info: Info) -> str:
        return str(info.context["example"])
```

Here we are returning a custom context dictionary that contains only one item
called "example".

Then we use the context in a resolver, the resolver will return "1" in this
case.

## get_root_value

`get_root_value` allows to provide a custom root value for your schema, this is
probably not used a lot but it might be useful in certain situations.

Here's an example:

```python
class MyGraphQLView(AsyncGraphQLView):
    async def get_root_value(self, request: HttpRequest) -> Any:
        return Query(name="Patrick")


@strawberry.type
class Query:
    name: str
```

Here we are returning a Query where the name is "Patrick", so we when requesting
the field name we'll return "Patrick" in this case.

## process_result

`process_result` allows to customize and/or process results before they are sent
to the clients. This can be useful logging errors or hiding them (for example to
hide internal exceptions).

It needs to return an object of `GraphQLHTTPResponse` and accepts the request
and the execution results.

```python
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from graphql.error import format_error as format_graphql_error

class MyGraphQLView(AsyncGraphQLView):
    async def process_result(
        self, request: HttpRequest, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [format_graphql_error(err) for err in result.errors]

        return data
```

In this case we are doing the default processing of the result, but it can be
tweaked based on your needs.

# Pagination in Django

Django provides numerous utilities to make common tasks in the web-development world easier.
It has it's own pagination API that is useful, when it comes to pagination with Strawberry.

-> **Note** You can check Django's docs regarding pagination [here](https://docs.djangoproject.com/en/3.2/topics/pagination/).

We've already covered how to do pagination in general. You can check our docs [here](/docs/guides/pagination)!

Let us try to implement the same example we did earlier, with Django's pagination API.
We want to request a list of users, 2 at a time, from a server.

We can model our schema like this:

```py
# example.py

from typing import List

import strawberry
from strawberry.types import Info


@strawberry.type
class User:
    name: str = strawberry.field(
        description="""
        The name of the user.
        """
    )

    occupation: str = strawberry.field(
        description="""
        The occupation of the user.
        """
    )

    age: int = strawberry.field(
        description="""
        The age of the user.
        """
    )


@strawberry.type
class PageMeta:
    total: int = strawberry.field(
        description="""
        The total number of items in the dataset.
        """
    )

    page: int = strawberry.field(
        description="""
        The current page number in the dataset.
        """
    )

    pages: int = strawberry.field(
        description="""
        The total number of pages in the dataset.
        """
    )


@strawberry.type
class UserResponse:
    users: List[User] = strawberry.field(
        description="""
        The list of users.
        """
    )

    page_meta: PageMeta = strawberry.field(
        description="""
        Metadata to aid in pagination.
        """
    )


@strawberry.type
class Query:
    @strawberry.field(description="Returns a list of users.")
    def get_users(self, info: Info) -> UserResponse:
        ...
```

For simplicity's sake, we'll use the same dataset used in the eariler example-
an in-memory list of hard-coded users.

```py
# example.py

user_data = [
  {
    "id": 1,
    "name": "Norman Osborn",
    "occupation": "Founder, Oscorp Industries",
    "age": 42
  },
  {
    "id": 2,
    "name": "Peter Parker",
    "occupation": "Freelance Photographer, The Daily Bugle",
    "age": 16
  },
  {
    "id": 3,
    "name": "Harold Osborn",
    "occupation": "President, Oscorp Industries",
    "age": 19
  },
  {
    "id": 4,
    "name": "Eddie Brock",
    "occupation": "Journalist, The Eddie Brock Report",
    "age": 20
  }
]
```

Implementing pagination is a breeze with Django's abstraction layers.

```py
# example.py

from typing import List, cast

import strawberry
from django.core.paginator import Paginator

# code omitted above for readability.

@strawberry.type
class Query:
    @strawberry.field(description="Returns a paginated list of users.")
    def get_users(self, info: Info, page_number: int, limit: int) -> UserResponse:
        # initialize the paginator.
        paginator = Paginator(user_data, per_page=limit)

        # get the relevant user data.
        sliced_users = paginator.get_page(page_number)

        # type cast the sliced data.
        sliced_users = cast(List[UserType], sliced_users)

        # calculate the total items present.
        total = paginator.count

        # calculate the client's current page number.
        page = sliced_users.number

        # calculate the total number of pages.
        pages = paginator.num_pages

        return UserResponse(
            users=sliced_users,
            page_meta=PageMeta(
                total=total,
                page=page,
                pages=pages
            )
        )
```

Now, let us plug our query into a schema and start a debug server!

```py
# example.py

from typing import List, cast

import strawberry

# code omitted above for readability.

@strawberry.type
class Query:
    @strawberry.field(description="Returns a paginated list of users.")
    def get_users(self, info: Info, page_number: int, limit: int) -> UserResponse:
        # initialize the paginator.
        paginator = Paginator(user_data, per_page=limit)

        # get the relevant user data.
        sliced_users = paginator.get_page(page_number)

        # type cast the sliced data.
        sliced_users = cast(List[UserType], sliced_users)

        # calculate the total items present.
        total = paginator.count

        # calculate the client's current page number.
        page = sliced_users.number

        # calculate the total number of pages.
        pages = paginator.num_pages

        return UserResponse(
            users=sliced_users,
            page_meta=PageMeta(
                total=total,
                page=page,
                pages=pages
            )
        )

schema = strawberry.Schema(query=Query)
```

```text
strawberry server example:schema
```

now, we should be able to query for users on the GraphiQL explorer!
Here's a sample query for you!

```graphql
query {
  getUsers {
    users {
      name
      occupation
    }
    pageMeta {
      total
      pages
    }
  }
}
```
