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

However, this method has a few drawbacks, too:

- It is not suitable for large datasets, because we need access to offset + limit number of items from the dataset, before discarding the offset
  and only returning the counted values.
- It doesn't work well in environments where records are frequently updated, the page window becomes inconsistent and unreliable. This often
  results in duplicate results and potentially skipping values.

### Cursor based pagination

Cursor-based pagination works by returning a pointer to a specific item in the dataset. On subsequent requests, the server returns results
after the given pointer. This method addresses the drawbacks of using offset pagination, but does so by making certain trade offs:

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

-> **Note** The cursor used during pagination need not always be a number. It is an
-> opaque value that the client may use to page through the result set.

## Implementing pagination in GraphQL

Now that we know a few of the common ways to implement pagination, let us look at how we can implement them in GraphQL.

-> **Note** There's also an official pagination guide provided by GraphQL. You can check it out [here](https://graphql.org/learn/pagination/)!

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
    @strawberry.field(description="Returns a list of users.")
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
    next_cursor: int = strawberry.field(
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
    @strawberry.field(description="Returns a list of users.")
    def get_users(self, info: Info, limit: int, cursor: Optional[int] = None) -> UserResponse:
        ...
```

The `get_users` field takes in two arguments, `limit` and `cursor`. Did you notice that the `cursor` argument is optional?
That's because the client doesn't know the cursor intiially, when it makes the first request.

Now is a good time to think of what we could use as a cursor for our dataset. Our cursor needs to be an opaque value,
which doesn't usually change over time. It makes more sense to use the IDs of the users as our cursor, as it fits both criteria.
Because our IDs are integers, our cursors will also be the same.

Using IDs as our cursor, we can implement our pagination logic like this:

```py
# example.py

from typing import List, Optional, cast

import strawberry
from strawberry.types import Info

# code omitted above for readability.

@strawberry.type
class Query:
    @strawberry.field(description="Returns a list of users.")
    def get_users(self, info: Info, limit: int, cursor: Optional[str] = None) -> UserResponse:
        return UserResponse(
            users=sliced_users,
            page_meta=PageMeta(
                next_cursor=next_cursor
            )
        )
```

## Controlling provided limits

You should always limit the maximum value of the `limit` or `offset` provided by the client (during offset-based
pagination). You could throw up an error when the given argument is above the expected size.

```py
import strawberry

@strawberry.type
class Query:
    @strawberry.field(description="Returns a paginated list of users.")
    def get_users(self, info: Info, offset: int, limit: int) -> UserResponse:
        # limit pagination arguments
        if len(limit) > 20:
            raise Exception("Requested limit is too high!")
```

It is also good practice to check if the provided limits are negative, and throw an error.

```py
import strawberry

@strawberry.type
class Query:
    @strawberry.field(description="Returns a paginated list of users.")
    def get_users(self, info: Info, offset: int, limit: int) -> UserResponse:
        # limit pagination arguments
        if len(limit) <= 0:
            raise Exception("Requested limit is too low!")
```
