---
title: Pagination - Cursor based
---

# Implementing Cursor Pagination

Next up, let's try to remodel our schema to use cursor-based pagination! The server needs to return a `cursor`
along with the sliced user data, so that our client can know what to query for next. The client could also provide
a `limit` value, to specify how much users it wants at a time.

Therefore, we could model our schema like this:

```py
# example.py

from typing import List, Optional

import strawberry
from strawberry.types import Info


# code omitted above for readability.

@strawberry.type
class PageMeta:
    next_cursor: Optional[str] = strawberry.field(
        description="""
        The next cursor to continue with.
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
    @strawberry.field(description="Get a list of users.")
    def get_users(self, info: Info, limit: int, cursor: Optional[str] = None) -> UserResponse:
        ...
```

The `get_users` field takes in two arguments, `limit` and `cursor`. Did you notice that the `cursor` argument is optional?
That's because the client doesn't know the cursor intiially, when it makes the first request.

Now is a good time to think of what we could use as a cursor for our dataset. Our cursor needs to be an opaque value,
which doesn't usually change over time. It makes more sense to use the IDs of the users as our cursor, as it fits both criteria.

It is good practice to base64-encode cursors, to provide a unified interface to the end user. API clients need not
bother about the type of data to paginate, and can pass unique IDs during pagination.

Let us define a couple of helper functions to encode and decode cursors as follows:

```py
# example.py

from base64 import b64encode, b64decode


def encode_user_cursor(id: int) -> str:
  """
  Encodes the given user ID into a cursor.

  :param id: The user ID to encode.

  :return: The encoded cursor.
  """
  return b64encode(f"user:{id}".encode("ascii")).decode("ascii")


def decode_user_cursor(cursor: str) -> int:
  """
  Decodes the user ID from the given cursor.

  :param cursor: The cursor to decode.

  :return: The decoded user ID.
  """
  cursor_data = b64decode(cursor.encode("ascii")).decode("ascii")
  return int(cursor_data.split(":")[1])
```

We can start implementing cursor pagination like this:

```py
# example.py

from typing import List, Optional, cast

import strawberry
from strawberry.types import Info

# code omitted above for readability.


@strawberry.type
class Query:
    @strawberry.field(description="Get a list of users.")
    def get_users(self, info: Info, limit: int, cursor: Optional[str] = None) -> UserResponse:
        if cursor is not None:
          # decode the user ID from the given cursor.
          user_id = decode_user_cursor(cursor=cursor)
        else:
          # no cursor was given (this happens usually when the
          # client sends a query for the first time).
          user_id = 0

        # filter the user data, going through the next set of results.
        filtered_data = map(lambda user: user.id > user_id, user_data)

        # slice the relevant user data (Here, we also slice an
        # additional user instance, to prepare the next cursor).
        sliced_users = filtered_data[:limit+1]

        if len(sliced_users) > limit:
          # calculate the client's next cursor.
          last_user = sliced_users.pop(-1)
          next_cursor = encode_user_cursor(id=last_user.id)
        else:
          # We have reached the last page, and
          # don't have the next cursor.
          next_cursor = None

        # type cast the sliced data.
        sliced_users = cast(List[UserType], sliced_users)

        return UserResponse(
            users=sliced_users,
            page_meta=PageMeta(
                next_cursor=next_cursor
            )
        )
```

Starting the debug server, we should be able to query for users again on the GraphiQL explorer.

```graphql
query {
  # we don't know the cursor initially
  getUsers(limit: 2) {
    users {
      name
      occupation
    }
    pageMeta {
      nextCursor
    }
  }
}
```
