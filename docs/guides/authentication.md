---
title: Authentication
---

# Authentication

Authentication is the process of verifying that a user is who they claim to be
and should be handled by the framework you are using. Some already have a
built-in authentication system (like Django); others, you have to provide it
manually. It's not Strawberry's responsibility to authenticate the user, but it
can be used to create a mutation that handles the authentication's process. It's
also very important not to confuse authentication with authorization:
authorization determines what an authenticated user can do or which data they
can access. In Strawberry, this is managed with
[`Permissions` classes](./permissions.md).

Let's see how to put together these concepts with an example. First, we define a
`login` mutation where we authenticate credentials and return `LoginSucces` or
`LoginError` types depending on whether the user was successfully authenticated
or not.

```python
import strawberry
from .types import User

from typing import Annotated, Union


@strawberry.type
class LoginSuccess:
    user: User


@strawberry.type
class LoginError:
    message: str


LoginResult = Annotated[
    Union[LoginSuccess, LoginError], strawberry.union("LoginResult")
]


@strawberry.type
class Mutation:
    @strawberry.field
    def login(self, username: str, password: str) -> LoginResult:
        # Your domain-specific authentication logic would go here
        user = ...

        if user is None:
            return LoginError(message="Something went wrong")

        return LoginSuccess(user=User(username=username))
```

### Access authenticated user in resolver

Its fairly common to require user information within a resolver. We can do that
in a type safe way with a custom context dataclass.

For example, in FastAPI this might look like this:

```python
from functools import cached_property

import strawberry
from fastapi import FastAPI
from strawberry.fastapi import BaseContext, GraphQLRouter


@strawberry.type
class User: ...  # This is just a stub for an actual user object


class Context(BaseContext):
    @cached_property
    def user(self) -> User | None:
        if not self.request:
            return None

        authorization = self.request.headers.get("Authorization", None)
        return authorization_service.authorize(authorization)


@strawberry.type
class Query:
    @strawberry.field
    def get_authenticated_user(self, info: strawberry.Info[Context]) -> User | None:
        return info.context.user


async def get_context() -> Context:
    return Context()


schema = strawberry.Schema(Query)


graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
)

app = FastAPI()
app.include_router(graphql_app, prefix="/graphql")
```
