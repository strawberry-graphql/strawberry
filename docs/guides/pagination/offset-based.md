---
title: Pagination - Offset based
---

# Implementing Offset Pagination

Let us start by implementing offset-based pagination first. We should be able to return a list of users which can be paginated by the client.
Let us model our schema like this:

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
