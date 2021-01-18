---
title: DataLoaders
---

# DataLoaders

Strawberry comes with a built-in DataLoader, a generic utility that can be used
to reduce the number of requests to databases or third party APIs by batching
and caching requests.

> Note: DataLoaders provide an async API, so they only work in async context

## Basic usage

Here's how you'd use a DataLoader, first we need to define a function that
allows to fetch data in batches. Let's say that we have a user type, that has
only an id:

```python
import strawberry

@strawberry.type
class User:
    id: strawberry.ID
```

we need to define a function that returns a list of users based on a list of keys
passed:

```python
from typing import List

async def load_users(keys: List[int]) -> List[User]:
    return [User(id=key) for key in keys]
```

Normally this function would interact with a database or 3rd party API, but for our
example we don't need that.

Now that we have a loader function, we can define a DataLoader and use it:

```python
from strawberry.dataloader import DataLoader

loader = DataLoader(load_fn=load_users)

user = await loader.load(1)
```

This will result in a call to `load_user` with keys equal to `[1]`. Where this becomes
really powerful is when you make multiple requests, like in this example:

```python
import asyncio

[user_a, user_b] = await asyncio.gather(loader.load(1), loader.load(2))
```

This will result in a call to `load_user` with keys equal to `[1, 2]`. Thus
reducing the number of calls to our database or 3rd party services to 1.

Additionally by default DataLoader caches the loads, so for example the
following code:

```python
await loader.load(1)
await loader.load(1)
```

Will result in only one call to `load_user`.

## Usage with GraphQL

Let's see an example of how you can use DataLoaders with GraphQL:

```python
import strawberry

@strawberry.type
class User:
    id: strawberry.ID

async def load_users(keys) -> List[User]:
    return [User(id=key) for key in keys]


loader = DataLoader(load_fn=load_user)

@strawberry.type
class Query:
    @strawberry.field
    async def get_user(self, id: strawberry.ID) -> User:
        return await loader.load(id)

schema = strawberry.Schema(query=Query)
```

Here we have defined the same loader as before, along side with a GraphQL query
that allows to fetch a single user by id.

We can use this query by doing the following request:

```graphql+response
{
  first: getUser(id: 1) {
    id
  }
  second: getUser(id: 2) {
    id
  }
}
---
{
  "data": {
    "first": {
      "id": 1
    },
    "second": {
      "id": 2
    }
  }
}
```

Even if this query is fetching two users, it still results in one call to
`load_users`.

## Usage with context

As you have seen in the code above, the dataloader is instantiated outside the
resolver, since we need to share it between multiple resolvers or even between
multiple resolver calls. However this is a not a recommended pattern when using your schema inside a server because the dataloader will so cache results for as long as the server is running.

Instead a common pattern is to create the dataloader when creating the GraphQL context so that it only caches results with a single request.
Let's see an example of this using our ASGI view:

```python
import strawberry
from strawberry.asgi import GraphQL
from strawberry.dataloder import DataLoader

from starlette.requests import Request
from starlette.websockets import WebSocket


@strawberry.type
class User:
    id: strawberry.ID


async def load_users(keys) -> List[User]:
    return [User(id=key) for key in keys]


class MyGraphQL(GraphQL):
    async def get_context(self, request: Union[Request, WebSocket]) -> Any:
        return {
            "user_loader": DataLoader(load_fn=load_user)
        }


@strawberry.type
class Query:
    @strawberry.field
    async def get_user(self, info, id: strawberry.ID) -> User:
        return await info.context["user_loader"].load(id)
```
