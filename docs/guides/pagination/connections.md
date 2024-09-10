---
title: Pagination - Implementing the Relay Connection Specification
---

# Implementing the Relay Connection Specification

We naively implemented cursor based pagination in the
[previous tutorial](./cursor-based.md). To ensure a consistent implementation of
this pattern, the Relay project has a formal
[specification](https://relay.dev/graphql/connections.htm) you can follow for
building GraphQL APIs which use a cursor based connection pattern.

By the end of this tutorial, we should be able to return a connection of users
when requested.

<CodeGrid>

```graphql
query getUsers {
  getUsers(first: 2) {
    users {
      edges {
        node {
          id
          name
          occupation
          age
        }
      }
      cursor
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
```

```json
{
  "data": {
    "getUsers": {
      "users": {
        "edges": [
          {
            "node": {
              "id": 1,
              "name": "Norman Osborn",
              "occupation": "Founder, Oscorp Industries",
              "age": 42
            },
            "cursor": "dXNlcjox"
          },
          {
            "node": {
              "id": 2,
              "name": "Peter Parker",
              "occupation": "Freelance Photographer, The Daily Bugle",
              "age": 20
            },
            "cursor": "dXNlcjoy"
          }
        ]
      },
      "pageInfo": {
        "endCursor": "dXNlcjoz",
        "hasNextPage": true
      }
    }
  }
}
```

</CodeGrid>

## Connections

A Connection represents a paginated relationship between two entities. This
pattern is used when the relationship itself has attributes. For example, we
might have a connection of users to represent a paginated list of users.

Let us define a Connection type which takes in a Generic ObjectType.

```py
# example.py

from typing import Generic, TypeVar

import strawberry


GenericType = TypeVar("GenericType")


@strawberry.type
class Connection(Generic[GenericType]):
    page_info: "PageInfo" = strawberry.field(
        description="Information to aid in pagination."
    )

    edges: list["Edge[GenericType]"] = strawberry.field(
        description="A list of edges in this connection."
    )
```

Connections must have atleast two fields: `edges` and `page_info`.

The `page_info` field contains metadata about the connection. Following the
Relay specification, we can define a `PageInfo` type like this:

```py line=22-38
# example.py

from typing import Generic, TypeVar

import strawberry


GenericType = TypeVar("GenericType")


@strawberry.type
class Connection(Generic[GenericType]):
    page_info: "PageInfo" = strawberry.field(
        description="Information to aid in pagination."
    )

    edges: list["Edge[GenericType]"] = strawberry.field(
        description="A list of edges in this connection."
    )


@strawberry.type
class PageInfo:
    has_next_page: bool = strawberry.field(
        description="When paginating forwards, are there more items?"
    )

    has_previous_page: bool = strawberry.field(
        description="When paginating backwards, are there more items?"
    )

    start_cursor: Optional[str] = strawberry.field(
        description="When paginating backwards, the cursor to continue."
    )

    end_cursor: Optional[str] = strawberry.field(
        description="When paginating forwards, the cursor to continue."
    )
```

You can read more about the `PageInfo` type at:

- https://graphql.org/learn/pagination/#pagination-and-edges
- https://relay.dev/graphql/connections.htm

The `edges` field must return a list type that wraps an edge type.

Following the Relay specification, let us define an Edge that takes in a generic
ObjectType.

```py line=41-49
# example.py

from typing import Generic, TypeVar

import strawberry


GenericType = TypeVar("GenericType")


@strawberry.type
class Connection(Generic[GenericType]):
    page_info: "PageInfo" = strawberry.field(
        description="Information to aid in pagination."
    )

    edges: list["Edge[GenericType]"] = strawberry.field(
        description="A list of edges in this connection."
    )


@strawberry.type
class PageInfo:
    has_next_page: bool = strawberry.field(
        description="When paginating forwards, are there more items?"
    )

    has_previous_page: bool = strawberry.field(
        description="When paginating backwards, are there more items?"
    )

    start_cursor: Optional[str] = strawberry.field(
        description="When paginating backwards, the cursor to continue."
    )

    end_cursor: Optional[str] = strawberry.field(
        description="When paginating forwards, the cursor to continue."
    )


@strawberry.type
class Edge(Generic[GenericType]):
    node: GenericType = strawberry.field(description="The item at the end of the edge.")

    cursor: str = strawberry.field(description="A cursor for use in pagination.")
```

EdgeTypes must have atleast two fields - `cursor` and `node`. Each edge has it's
own cursor and item (represented by the `node` field).

Now that we have the types needed to implement pagination using Relay
Connections, let us use them to paginate a list of users. For simplicity's sake,
let our dataset be a list of dictionaries.

```py line=7-32
# example.py

from typing import Generic, TypeVar

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


GenericType = TypeVar("GenericType")


@strawberry.type
class Connection(Generic[GenericType]):
    page_info: "PageInfo" = strawberry.field(
        description="Information to aid in pagination."
    )

    edges: list["Edge[GenericType]"] = strawberry.field(
        description="A list of edges in this connection."
    )


@strawberry.type
class PageInfo:
    has_next_page: bool = strawberry.field(
        description="When paginating forwards, are there more items?"
    )

    has_previous_page: bool = strawberry.field(
        description="When paginating backwards, are there more items?"
    )

    start_cursor: Optional[str] = strawberry.field(
        description="When paginating backwards, the cursor to continue."
    )

    end_cursor: Optional[str] = strawberry.field(
        description="When paginating forwards, the cursor to continue."
    )


@strawberry.type
class Edge(Generic[GenericType]):
    node: GenericType = strawberry.field(description="The item at the end of the edge.")

    cursor: str = strawberry.field(description="A cursor for use in pagination.")
```

Now is a good time to think of what we could use as a cursor for our dataset.
Our cursor needs to be an opaque value, which doesn't usually change over time.
It makes sense to use base64 encoded IDs of users as our cursor, as they fit
both criteria.

<Tip>

While working with Connections, it is a convention to base64-encode cursors. It
provides a unified interface to the end user. API clients need not bother about
the type of data to paginate, and can pass unique IDs during pagination. It also
makes the cursors opaque.

</Tip>

Let us define a couple of helper functions to encode and decode cursors as
follows:

```py line=3,35-43
# example.py

from base64 import b64encode, b64decode
from typing import Generic, TypeVar

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


GenericType = TypeVar("GenericType")


@strawberry.type
class Connection(Generic[GenericType]):
    page_info: "PageInfo" = strawberry.field(
        description="Information to aid in pagination."
    )

    edges: list["Edge[GenericType]"] = strawberry.field(
        description="A list of edges in this connection."
    )


@strawberry.type
class PageInfo:
    has_next_page: bool = strawberry.field(
        description="When paginating forwards, are there more items?"
    )

    has_previous_page: bool = strawberry.field(
        description="When paginating backwards, are there more items?"
    )

    start_cursor: Optional[str] = strawberry.field(
        description="When paginating backwards, the cursor to continue."
    )

    end_cursor: Optional[str] = strawberry.field(
        description="When paginating forwards, the cursor to continue."
    )


@strawberry.type
class Edge(Generic[GenericType]):
    node: GenericType = strawberry.field(description="The item at the end of the edge.")

    cursor: str = strawberry.field(description="A cursor for use in pagination.")
```

Let us define a `get_users` field which returns a connection of users, as well
as an `UserType`. Let us also plug our query into a schema.

```python line=104-174
# example.py

from base64 import b64encode, b64decode
from typing import List, Optional, Generic, TypeVar

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


GenericType = TypeVar("GenericType")


@strawberry.type
class Connection(Generic[GenericType]):
    page_info: "PageInfo" = strawberry.field(
        description="Information to aid in pagination."
    )

    edges: list["Edge[GenericType]"] = strawberry.field(
        description="A list of edges in this connection."
    )


@strawberry.type
class PageInfo:
    has_next_page: bool = strawberry.field(
        description="When paginating forwards, are there more items?"
    )

    has_previous_page: bool = strawberry.field(
        description="When paginating backwards, are there more items?"
    )

    start_cursor: Optional[str] = strawberry.field(
        description="When paginating backwards, the cursor to continue."
    )

    end_cursor: Optional[str] = strawberry.field(
        description="When paginating forwards, the cursor to continue."
    )


@strawberry.type
class Edge(Generic[GenericType]):
    node: GenericType = strawberry.field(description="The item at the end of the edge.")

    cursor: str = strawberry.field(description="A cursor for use in pagination.")


@strawberry.type
class User:
    id: int = strawberry.field(description="The id of the user.")

    name: str = strawberry.field(description="The name of the user.")

    occupation: str = strawberry.field(description="The occupation of the user.")

    age: int = strawberry.field(description="The age of the user.")


@strawberry.type
class Query:
    @strawberry.field(description="Get a list of users.")
    def get_users(
        self, first: int = 2, after: Optional[str] = None
    ) -> Connection[User]:
        if after is not None:
            # decode the user ID from the given cursor.
            user_id = decode_user_cursor(cursor=after)
        else:
            # no cursor was given (this happens usually when the
            # client sends a query for the first time).
            user_id = 0

        # filter the user data, going through the next set of results.
        filtered_data = list(filter(lambda user: user["id"] > user_id, user_data))

        # slice the relevant user data (Here, we also slice an
        # additional user instance, to prepare the next cursor).
        sliced_users = filtered_data[: first + 1]

        if len(sliced_users) > first:
            # calculate the client's next cursor.
            last_user = sliced_users.pop(-1)
            next_cursor = encode_user_cursor(id=last_user["id"])
            has_next_page = True
        else:
            # We have reached the last page, and
            # don't have the next cursor.
            next_cursor = None
            has_next_page = False

        # We know that we have items in the
        # previous page window if the initial user ID
        # was not the first one.
        has_previous_page = user_id > 0

        # build user edges.
        edges = [
            Edge(
                node=User(**user),
                cursor=encode_user_cursor(id=user["id"]),
            )
            for user in sliced_users
        ]

        if edges:
            # we have atleast one edge. Get the cursor
            # of the first edge we have.
            start_cursor = edges[0].cursor
        else:
            # We have no edges to work with.
            start_cursor = None

        if len(edges) > 1:
            # We have atleast 2 edges. Get the cursor
            # of the last edge we have.
            end_cursor = edges[-1].cursor
        else:
            # We don't have enough edges to work with.
            end_cursor = None

        return Connection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next_page,
                has_previous_page=has_previous_page,
                start_cursor=start_cursor,
                end_cursor=end_cursor,
            ),
        )


schema = strawberry.Schema(query=Query)
```

you can start the debug server with the following command:

```shell
strawberry server example:schema
```

Here's an example query to try out:

```graphql
query getUsers {
  getUsers(first: 2) {
    edges {
      node {
        id
        name
        occupation
        age
      }
      cursor
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
```
