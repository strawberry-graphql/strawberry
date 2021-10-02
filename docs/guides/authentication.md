---
title: Authentication
---

# Authentication

Authentication is the process of verifying that a user is "whom they claim to be" and
should be handled by the framework you are using. Some already have a built-in
authentication system (like Django); others, you have to provide it manually. It's not
Strawberry's responsibility to authenticate the user, but it can provide some
surroundings to the real authentication process. It's also very important to not confuse
authentication with authorization: authorization determines "what an authenticated user
is allowed to do or which data he/she can access to". In Strawberry, this is done with
[`Permissions` classes](./permissions.md).

Let's see how to put toghether these concepts with an example. First, we define a `login`
mutation where we authenticate credentials and return `LoginSucces` or `LoginError` types
depending on whether the user was successfully authenticated or not.

```python
import strawberry
from .types import User


@strawberry.type
class LoginSuccess:
    user: User


@strawberry.type
class LoginError:
    message: str = None


LoginResult = strawberry.union("LoginResult", (LoginSuccess, LoginError))


@strawberry.type
class Mutation:
    @strawberry.field
    def login(self, username: str, password: str) -> LoginResult:

        # Your domain-specific authentication logic would go here
        user = ...

        if user is not None:
            return LoginSuccess(user=User(username=username))
        else:
            return LoginError(message="Something went wrong")
```
