---
title: DataLoaders
---

# DataLoaders

Strawberry comes with a built-in DataLoader, a generic utility that can be used
to reduce the number of requests to databases or third party APIs by batching
and caching requests.

<Note>

DataLoaders provide an async API, so they only work in async context

</Note>

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

we need to define a function that returns a list of users based on a list of
keys passed:

```python
from typing import List

async def load_users(keys: List[int]) -> List[User]:
    return [User(id=key) for key in keys]
```

Normally this function would interact with a database or 3rd party API, but for
our example we don't need that.

Now that we have a loader function, we can define a DataLoader and use it:

```python
from strawberry.dataloader import DataLoader

loader = DataLoader(load_fn=load_users)

user = await loader.load(1)
```

This will result in a call to `load_users` with keys equal to `[1]`. Where this
becomes really powerful is when you make multiple requests, like in this
example:

```python
import asyncio

[user_a, user_b] = await asyncio.gather(loader.load(1), loader.load(2))
```

This will result in a call to `load_users` with keys equal to `[1, 2]`. Thus
reducing the number of calls to our database or 3rd party services to 1.

Additionally by default DataLoader caches the loads, so for example the
following code:

```python
await loader.load(1)
await loader.load(1)
```

Will result in only one call to `load_users`.

And finally sometimes we'll want to load more than one key at a time. In those
cases we can use the `load_many` method.

```python
[user_a, user_b, user_c] = await loader.load_many([1, 2, 3])
```

### Errors

An error associated with a particular key can be indicated by including an
exception value in the corresponding position in the returned list. This
exception will be thrown by the `load` call for that key. With the same `User`
class from above:

```python
from typing import List, Union
from strawberry.dataloader import DataLoader

users_database = {
    1: User(id=1),
    2: User(id=2),
}

async def load_users(keys: List[int]) -> List[Union[User, ValueError]]:
    def lookup(key: int) -> Union[User, ValueError]:
       if user := users_database.get(key):
           return user

       return ValueError("not found")

    return [lookup(key) for key in keys]

loader = DataLoader(load_fn=load_users)
```

For this loader, calls like `await loader.load(1)` will return `User(id=1)`,
while `await loader.load(3)` will raise `ValueError("not found")`.

It's important that the `load_users` function returns exception values within
the list for each incorrect key. A call with `keys == [1, 3]` returns
`[User(id=1), ValueError("not found")]`, and doesn't raise the `ValueError`
directly. If the `load_users` function raises an exception, even `load`s with an
otherwise valid key, like `await loader.load(1)`, will raise that exception.

### Cache invalidation

By default DataLoaders use an internal cache. It is great for performance, however it can cause problems when the data is modified
(i.e., a mutation), as the cached data is no longer be valid! 😮

To fix it, you can explicitly invalidate the data in the cache, using one of these ways:

- Specifying a key with `loader.clear(id)`,
- Specifying several keys with `loader.clear_many([id1, id2, id3, ...])`,
- Invalidating the whole cache with `loader.clear_all()`

### Importing data into cache

While dataloaders are powerful and efficient, they do not support complex queries.

If your app needs them, you'll probably mix dataloaders and direct database calls.

In these scenarios, it is useful to import the data retrieved externally into the dataloader,
in order to avoid reloading data afterwards.

For example:

```python+graphql
@strawberry.type
class Person:
    id: strawberry.ID
    friends_ids: strawberry.Private[List[strawberry.ID]]

    @strawberry.field
    async def friends(self) -> List[Person]:
      return await loader.load_many(self.friends_ids)

@strawberry.type
class Query:
    @strawberry.field
    async def get_all_people(self) -> List[User]:
        # Fetch all people from the database, without going through the dataloader abstraction
        people = await database.get_all_people()

        # Insert the people we fetched in the dataloader cache
        # Since "all people" are now in the cache, accessing `Person.friends` will not
        # trigger any extra database access
        loader.prime_many({person.id: person for person in people})

        return people
---
{
  getAllPeople {
    id
    friends {
      id
    }
  }
}
```

## Usage with GraphQL

Let's see an example of how you can use DataLoaders with GraphQL:

```python
from typing import List

from strawberry.dataloader import DataLoader
import strawberry

@strawberry.type
class User:
    id: strawberry.ID

async def load_users(keys) -> List[User]:
    return [User(id=key) for key in keys]


loader = DataLoader(load_fn=load_users)

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
multiple resolver calls. However this is a not a recommended pattern when using
your schema inside a server because the dataloader will cache results for as
long as the server is running.

Instead a common pattern is to create the dataloader when creating the GraphQL
context so that it only caches results with a single request. Let's see an
example of this using our ASGI view:

```python
from typing import List, Union, Any, Optional

import strawberry
from strawberry.types import Info
from strawberry.asgi import GraphQL
from strawberry.dataloader import DataLoader

from starlette.requests import Request
from starlette.websockets import WebSocket
from starlette.responses import Response


@strawberry.type
class User:
    id: strawberry.ID


async def load_users(keys) -> List[User]:
    return [User(id=key) for key in keys]


class MyGraphQL(GraphQL):
    async def get_context(self, request: Union[Request, WebSocket], response: Optional[Response]) -> Any:
        return {
            "user_loader": DataLoader(load_fn=load_users)
        }


@strawberry.type
class Query:
    @strawberry.field
    async def get_user(self, info: Info, id: strawberry.ID) -> User:
        return await info.context["user_loader"].load(id)


schema = strawberry.Schema(query=Query)
app = MyGraphQL(schema)
```

You can now run the example above with any ASGI server, you can read [ASGI](../integrations/asgi.md)) to
get more details on how to run the app.
In case you choose uvicorn you can install it wih

```bash
pip install uvicorn
```

and then, assuming we named our file above `schema.py` we start the app with

```
uvicorn schema:app
```
