---
title: Pagination - Cursor based
---

# Implementing Cursor Pagination

Make sure to check our introduction to pagination [here](./overview.md)!

Let us implement cursor based pagination in GraphQL. By the end of this
tutorial, we should be able to return a paginated list of users when requested.

<CodeGrid>

```graphql
query getUsers {
  getUsers(limit: 2) {
    users {
      id
      name
      occupation
      age
    }
    pageMeta {
      nextCursor
    }
  }
}
```

```json
{
  "data": {
    "getUsers": {
      "users": [
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
          "age": 20
        }
      ],
      "pageMeta": {
        "nextCursor": "dXNlcjoz"
      }
    }
  }
}
```

</CodeGrid>

The server needs to return a `cursor` along with the sliced user data, so that
our client can know what to query for next. The client could also provide a
`limit` value, to specify how much users it wants at a time.

Let us model our schema like this:

```py
# example.py

from typing import List, Optional, Dict, Any, cast

import strawberry


@strawberry.type
class User:
    id: str = strawberry.field(description="ID of the user.")
    name: str = strawberry.field(description="The name of the user.")
    occupation: str = strawberry.field(description="The occupation of the user.")
    age: int = strawberry.field(description="The age of the user.")

    @staticmethod
    def from_row(row: Dict[str, Any]) -> "User":
        return User(
            id=row["id"], name=row["name"], occupation=row["occupation"], age=row["age"]
        )


@strawberry.type
class PageMeta:
    next_cursor: Optional[str] = strawberry.field(
        description="The next cursor to continue with."
    )


@strawberry.type
class UserResponse:
    users: List[User] = strawberry.field(description="The list of users.")

    page_meta: PageMeta = strawberry.field(description="Metadata to aid in pagination.")


@strawberry.type
class Query:
    @strawberry.field(description="Get a list of users.")
    def get_users(self) -> UserResponse: ...


schema = strawberry.Schema(query=Query)
```

For simplicity's sake, our dataset is going to be an in-memory list.

```py line=7-32
# example.py

from typing import List, Optional, Dict, Any, cast

import strawberry

user_data = [
    {
        "id": 1,
        "name": "Norman Osborn",
        "occupation": "Founder, Oscorp Industries",
        "age": 42,
    },
    {
        "id": 2,
        "name": "Peter Parker",
        "occupation": "Freelance Photographer, The Daily Bugle",
        "age": 20,
    },
    {
        "id": 3,
        "name": "Harold Osborn",
        "occupation": "President, Oscorp Industries",
        "age": 19,
    },
    {
        "id": 4,
        "name": "Eddie Brock",
        "occupation": "Journalist, The Eddie Brock Report",
        "age": 20,
    },
]


@strawberry.type
class User:
    id: str = strawberry.field(description="ID of the user.")
    name: str = strawberry.field(description="The name of the user.")
    occupation: str = strawberry.field(description="The occupation of the user.")
    age: int = strawberry.field(description="The age of the user.")

    @staticmethod
    def from_row(row: Dict[str, Any]) -> "User":
        return User(
            id=row["id"], name=row["name"], occupation=row["occupation"], age=row["age"]
        )


@strawberry.type
class PageMeta:
    next_cursor: Optional[str] = strawberry.field(
        description="The next cursor to continue with."
    )


@strawberry.type
class UserResponse:
    users: List[User] = strawberry.field(description="The list of users.")
    page_meta: PageMeta = strawberry.field(description="Metadata to aid in pagination.")


@strawberry.type
class Query:
    @strawberry.field(description="Get a list of users.")
    def get_users(self) -> UserResponse: ...


schema = strawberry.Schema(query=Query)
```

Now is a good time to think of what we could use as a cursor for our dataset.
Our cursor needs to be an opaque value, which doesn't usually change over time.
It makes sense to use base64 encoded IDs of users as our cursor, as they fit
both criteria.

<Tip>

It is good practice to base64-encode cursors, to provide a unified interface to
the end user. API clients need not bother about the type of data to paginate,
and can pass unique IDs during pagination. It also makes the cursor opaque.

</Tip>

Let us define a couple of helper functions to encode and decode cursors as
follows:

```py line=3,35-43
# example.py

from base64 import b64encode, b64decode
from typing import List, Optional, Dict, Any, cast

import strawberry

user_data = [
    {
        "id": 1,
        "name": "Norman Osborn",
        "occupation": "Founder, Oscorp Industries",
        "age": 42,
    },
    {
        "id": 2,
        "name": "Peter Parker",
        "occupation": "Freelance Photographer, The Daily Bugle",
        "age": 20,
    },
    {
        "id": 3,
        "name": "Harold Osborn",
        "occupation": "President, Oscorp Industries",
        "age": 19,
    },
    {
        "id": 4,
        "name": "Eddie Brock",
        "occupation": "Journalist, The Eddie Brock Report",
        "age": 20,
    },
]


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


@strawberry.type
class User:
    id: str = strawberry.field(description="ID of the user.")
    name: str = strawberry.field(description="The name of the user.")
    occupation: str = strawberry.field(description="The occupation of the user.")
    age: int = strawberry.field(description="The age of the user.")

    @staticmethod
    def from_row(row: Dict[str, Any]) -> "User":
        return User(
            id=row["id"], name=row["name"], occupation=row["occupation"], age=row["age"]
        )


@strawberry.type
class PageMeta:
    next_cursor: Optional[str] = strawberry.field(
        description="The next cursor to continue with."
    )


@strawberry.type
class UserResponse:
    users: List[User] = strawberry.field(description="The list of users.")
    page_meta: PageMeta = strawberry.field(description="Metadata to aid in pagination.")


@strawberry.type
class Query:
    @strawberry.field(description="Get a list of users.")
    def get_users(self) -> UserResponse: ...


schema = strawberry.Schema(query=Query)
```

We're going to use the dataset we defined in our `get_users` field resolver. Our
field is going to accept two arguments, `limit` and `cursor`, to control
pagination. Let us implement the pagination logic as follows.

Now, let us implement the pagination logic.

```py line=79-115
# example.py

from base64 import b64encode, b64decode
from typing import List, Optional, Dict, Any, cast

import strawberry

user_data = [
    {
        "id": 1,
        "name": "Norman Osborn",
        "occupation": "Founder, Oscorp Industries",
        "age": 42,
    },
    {
        "id": 2,
        "name": "Peter Parker",
        "occupation": "Freelance Photographer, The Daily Bugle",
        "age": 20,
    },
    {
        "id": 3,
        "name": "Harold Osborn",
        "occupation": "President, Oscorp Industries",
        "age": 19,
    },
    {
        "id": 4,
        "name": "Eddie Brock",
        "occupation": "Journalist, The Eddie Brock Report",
        "age": 20,
    },
]


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


@strawberry.type
class User:
    id: str = strawberry.field(description="ID of the user.")
    name: str = strawberry.field(description="The name of the user.")
    occupation: str = strawberry.field(description="The occupation of the user.")
    age: int = strawberry.field(description="The age of the user.")

    @staticmethod
    def from_row(row: Dict[str, Any]) -> "User":
        return User(
            id=row["id"], name=row["name"], occupation=row["occupation"], age=row["age"]
        )


@strawberry.type
class PageMeta:
    next_cursor: Optional[str] = strawberry.field(
        description="The next cursor to continue with."
    )


@strawberry.type
class UserResponse:
    users: List[User] = strawberry.field(description="The list of users.")
    page_meta: PageMeta = strawberry.field(description="Metadata to aid in pagination.")


@strawberry.type
class Query:
    @strawberry.field(description="Get a list of users.")
    def get_users(self, limit: int, cursor: Optional[str] = None) -> UserResponse:
        if cursor is not None:
            # decode the user ID from the given cursor.
            user_id = decode_user_cursor(cursor=cursor)
        else:
            # no cursor was given (this happens usually when the
            # client sends a query for the first time).
            user_id = 0

        # filter the user data, going through the next set of results.
        filtered_data = [user for user in user_data if user["id"] >= user_id]

        # slice the relevant user data (Here, we also slice an
        # additional user instance, to prepare the next cursor).
        sliced_users = filtered_data[: limit + 1]

        if len(sliced_users) > limit:
            # calculate the client's next cursor.
            last_user = sliced_users.pop(-1)
            next_cursor = encode_user_cursor(id=last_user["id"])
        else:
            # We have reached the last page, and
            # don't have the next cursor.
            next_cursor = None

        sliced_users = [User.from_row(x) for x in sliced_users]

        return UserResponse(
            users=sliced_users, page_meta=PageMeta(next_cursor=next_cursor)
        )


schema = strawberry.Schema(query=Query)
```

<Note>

Did you notice that cursor argument we defined is optional? That's because the
client doesn't know the cursor initially, when it makes the first request.

</Note>

Now, let us start a debug server with our schema!

```shell
strawberry server example:schema
```

We should be able to query for users on the GraphiQL explorer. Here's a sample
query for you!

```graphql
query getUsers {
  getUsers(limit: 2) {
    users {
      id
      name
      occupation
      age
    }
    pageMeta {
      nextCursor
    }
  }
}
```
