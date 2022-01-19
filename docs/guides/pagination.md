---
title: Pagination
---

# Pagination

Whenever we deal with lists in GraphQL, we usually need to limit the number of items returned. Surely, we don't want to send massive lists of
items that take a considerable toll on the server! The goal of this guide is to help you get going fast with pagination!

## Pagination at a glance

We have always dealt with pagination in different situations. Let us take a look at some of the common ways pagination
can be implemented today!

### Offset based pagination

This pagination style is similar to the syntax we use when looking up database records. Here, the client specifies the number of result to be
obtained at a time, along with an offset- which usually denotes the number of results to be skipped from the beginning. This type of pagination
is widely used. Implementing offset-based pagination with an SQL database is straight-forward:

- We count all of the results to determine the total number of pages
- We use the limit and offset values given to query for the items in the requested page.

Offset based pagination also provides us the ability to jump to a specific page in a dataset.

Let us understand offset based pagination better, with an example. Let us assume that we want to request a list of users, 2 at a time, from a server.
We start out be sending a request to the server, with the desired limit and offset values.

```json
{
  "limit": 2,
  "offset": 0
}
```

The response from the server would be:

```json
{
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
      "age": 16
    }
  ],
  "page_meta": {
    "total": 4,
    "page": 1,
    "pages": 2
  }
}
```

Where `total` is the total number of items on all pages, `page` is the current page and `pages` is the total number of pages available.
To get the next page in the dataset, we can send another request, incrementing the offset by the existing limit.

```json
{
  "limit": 2,
  "offset": 2
}
```

<Note>
Offset based pagination has a few limitations:

- It is not suitable for large datasets, because we need access to offset + limit number of items from the dataset, before discarding the offset
  and only returning the counted values.
- It doesn't work well in environments where records are frequently updated, the page window becomes inconsistent and unreliable. This often
  results in duplicate results and potentially skipping values.

However, it provides a quick way to get started, and works well with small-medium datasets. When your dataset scales, you will
need a reliable and consistent way to handle pagination.
</Note>

### Cursor based pagination

Cursor-based pagination, also known as keyset pagination, works by returning a pointer to a specific item in the dataset. On subsequent requests,
the server returns results after the given pointer. This method addresses the drawbacks of using offset pagination, but does so by making certain trade offs:

- The cursor must be based on a unique, sequential identifier in the given source.
- There is no concept of the total number of pages or results in the dataset.
- The client can’t jump to a specific page.

Let us understand cursor based pagination better, with the example given below. We want to request a list of users, 2 at a time, from
the server. We don't know the cursor initially, so we will assign it a null value.

```json
{
  "limit": 2,
  "cursor": null
}
```

The response from the server would be:

```json
{
  "users": [
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
  ],
  "next_cursor": "3"
}
```

The next cursor returned by the server can be used to get the next set of users from the server.

```json
{
  "limit": 2,
  "cursor": "3"
}
```

This is an example for forward pagination - pagination can be done backwards too!

## Implementing pagination in GraphQL

Now that we know a few of the common ways to implement pagination, let us look at how we can implement them in GraphQL.

-> **Note** The GraphQL specification [recommends cursor-based pagination](https://graphql.org/learn/pagination/) and
-> refers to [Relay's Connection specification](https://relay.dev/graphql/connections.htm) for specific implementation details.
-> We'll learn more about that later in this guide!

Let us start by implementing offset-based pagination first. We should be able to return a list of users which can be paginated by the client.
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
    @strawberry.field(description="Get a list of users.")
    def get_users(self, info: Info) -> UserResponse:
        ...

```

As you can see above, we have modelled our field's return type to return additional fields, rather than an ordinary list.
The client can query the provided object types (PageMeta) in order to know more about the dataset.

now, it is time to implement pagination. For simplicity's sake, our dataset is going to be an in-memory list.

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

We're going to use the data in our `get_users` field resolver.
Our field is going to accept two arguments, `limit` and `offset`, to control pagination.

```py
# example.py

from typing import List, cast

import strawberry

# code omitted above for readability.

@strawberry.type
class Query:
    @strawberry.field(description="Returns a paginated list of users.")
    def get_users(self, info: Info, offset: int, limit: int) -> UserResponse:
        # slice the relevant user data.
        sliced_users = user_data[offset:offset+limit]

        # type cast the sliced data.
        sliced_users = cast(List[UserType], sliced_users)

        # calculate the total items present.
        total = len(user_data)

        # calculate the client's current page number.
        page = ceil((offset-1) / limit) + 1

        # calculate the total number of pages.
        pages = ceil(total / limit)

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
    def get_users(self, info: Info, offset: int, limit: int) -> UserResponse:
        # slice the relevant user data.
        sliced_users = user_data[offset:offset+limit]

        # type cast the sliced data.
        sliced_users = cast(List[UserType], sliced_users)

        # calculate the total items present.
        total = len(user_data)

        # calculate the client's current page number.
        page = ceil((offset-1) / limit) + 1

        # calculate the total number of pages.
        pages = ceil(total / limit)

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
  getUsers(offset: 0, limit: 2) {
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

## Working with Relay Connections

The GraphQL specification [recommends cursor-based pagination](https://graphql.org/learn/pagination/) and refers
to [Relay's Connection specification](https://relay.dev/graphql/connections.htm) for specific implementation details.

### Connections

A Connection represents a paginated relationship between two entities. This pattern is used when the relationship
itself has attributes. For example, we might have a connection of users to represent a paginated list of users.

Let us define a Connection type which takes in a Generic ObjectType.

```py
# example.py

from typing import Generic, TypeVar
import strawberry


GenericType = TypeVar("GenericType")


@strawberry.type
class Connection(Generic[GenericType]):
    page_info: "PageInfo" = strawberry.field(
      description="""
      Information to aid in pagination.
      """
    )

    edges: list["Edge[GenericType]"] = strawberry.field(
      description="""
      A list of edges in this connection.
      """
    )

```

Connections must have atleast two fields - `edges` and `page_info`.

The `page_info` field contains metadata about the connection.
Following the Relay specification, we can define a `PageInfo` type like this:

```py
# example.py

# code omitted above for readability.

@strawberry.type
class PageInfo:
    has_next_page: bool = strawberry.field(
      description="""
      When paginating forwards, are there more items?
      """
    )

    has_previous_page: bool = strawberry.field(
      description="""
      When paginating backwards, are there more items?
      """
    )

    start_cursor: Optional[str] = strawberry.field(
      description="""
      When paginating backwards, the cursor to continue.
      """
    )

    end_cursor: Optional[str] = strawberry.field(
      description="""
      When paginating forwards, the cursor to continue.
      """
    )

```

You can read more about the `PageInfo` type at:

- https://graphql.org/learn/pagination/#pagination-and-edges
- https://relay.dev/graphql/connections.htm

The `edges` field must return a list type that wraps an edge type.

Following the Relay specification, let us define an Edge that takes
in a generic ObjectType.

```py
# example.py

# code omitted above for readability.

@strawberry.type
class Edge(Generic[GenericType]):
    node: GenericType = strawberry.field(
      description="""
      The item at the end of the edge.
      """
    )

    cursor: str = strawberry.field(
      description="""
      A cursor for use in pagination.
      """
    )

```

EdgeTypes must have atleast two fields - `cursor` and `node`. The field names are self-explanatory.
Each edge has it's own cursor and item (represented by the `node` field).

Now that we have the types needed to implement pagination using Relay Connections, let
us use them to paginate a list of users. As seen in the previous examples, let our dataset be a
list of dictionaries.

```py
# example.py

# code omitted above for readability.

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

Let us also make use of helpers to encode/ decode cursors, as seen in the
previous examples.

```py
# example.py

from base64 import b64encode, b64decode

# code omitted above for readability.


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

Let us define a `get_users` field which returns a connection of users.

```python
# example.py

from typing import List, Optional
import strawberry

# code omitted above for readability.

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
class Query:
    @strawberry.field(description="Get a list of users.")
    def get_users(self, first: int = 2, after: Optional[str] = None) -> Connection[User]:
        if after is not None:
          # decode the user ID from the given cursor.
          user_id = decode_user_cursor(cursor=after)
        else:
          # no cursor was given (this happens usually when the
          # client sends a query for the first time).
          user_id = 0

        # filter the user data, going through the next set of results.
        filtered_data = map(lambda user: user.id > user_id, user_data)

        # slice the relevant user data (Here, we also slice an
        # additional user instance, to prepare the next cursor).
        sliced_users = filtered_data[after:first+1]

        if len(sliced_users) > first:
          # calculate the client's next cursor.
          last_user = sliced_users.pop(-1)
          next_cursor = encode_user_cursor(id=last_user.id)
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
            node=cast(UserType, user),
            cursor=encode_user_cursor(id=user.id),
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
            )
        )

schema = strawberry.Schema(query=Query)
```

you can start the debug server with the following command:

```
strawberry server example:schema
```

Here's an example query to try out:

```graphql
{
  getUsers {
    pageInfo {
      hasNextPage
      hasPreviousPage
      startCursor
      endCursor
    }
    edges {
      node {
        name
        occupation
        age
      }
      cursor
    }
  }
}
```
