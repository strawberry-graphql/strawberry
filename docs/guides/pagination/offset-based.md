---
title: Pagination - Offset based
---

# Implementing Offset Pagination

Make sure to check our introduction to pagination [here](./overview.md)!

Let us implement offset based pagination in GraphQL. By the end of this tutorial, we
should be able to return a paginated list of users when requested.

```graphql+response
query getUsers {
  getUsers(offset: 0, limit: 2) {
    users {
      id
      name
      occupation
      age
    }
    pageMeta {
      total
      pages
    }
  }
}
---
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
          "age": 16
        }
      ],
      "pageMeta": {
          "total": 4,
          "page": 1,
          "pages": 2
      }
    }
  }
}
```

Let us model our schema like this:

```py
# example.py

from typing import List

import strawberry


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
    def get_users(self) -> UserResponse:
        ...

schema = strawberry.Schema(query=Query)

```

As you can see above, we have modeled our field to return an object type, rather than a list.
The return type contains additional metadata that the client can query for, to know more about the paginated list.

For simplicity's sake, our dataset is going to be an in-memory list.

```py line=7-32
# example.py

from typing import List

import strawberry

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
    def get_users(self) -> UserResponse:
        ...

schema = strawberry.Schema(query=Query)

```

We're going to use the dataset we defined in our `get_users` field resolver.
Our field is going to accept two arguments, `limit` and `offset`, to control pagination.
Let us implement the pagination logic as follows.

```py line=76-116
# example.py

from typing import List

import strawberry

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
    @strawberry.field(description="Returns a paginated list of users.")
    def get_users(self, offset: int, limit: int) -> UserResponse:
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

<Tip>

If you're using Strawberry with the Django web framework, you might want to make use of the
Django pagination API. You can check it out [here](https://docs.djangoproject.com/en/4.0/topics/pagination/).

</Tip>

Now, let us start a debug server with our schema!

```text
strawberry server example:schema
```

We should be able to query for users on the GraphiQL explorer. Here's a sample query for you!

```graphql
query getUsers {
  getUsers(offset: 0, limit: 2) {
    users {
      id
      name
      occupation
      age
    }
    pageMeta {
      total
      pages
    }
  }
}
```
