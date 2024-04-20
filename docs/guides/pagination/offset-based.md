---
title: Pagination - Offset based
---

# Implementing Offset-Based Pagination

Make sure to check our introduction to pagination [here](./overview.md)!

Let us implement offset-based pagination in GraphQL. By the end of this
tutorial, we should be able to return a sorted, filtered, and paginated list of
users.

Let us model the `User` type, which represents one user, with a name,
occupation, and age.

```python
# example.py
from typing import List, TypeVar, Dict, Any, Generic
import strawberry


@strawberry.type
class User:
    name: str = strawberry.field(description="The name of the user.")
    occupation: str = strawberry.field(description="The occupation of the user.")
    age: int = strawberry.field(description="The age of the user.")

    @staticmethod
    def from_row(row: Dict[str, Any]):
        return User(name=row["name"], occupation=row["occupation"], age=row["age"])
```

Let us now model the `PaginationWindow`, which represents one "slice" of sorted,
filtered, and paginated items.

```python
Item = TypeVar("Item")


@strawberry.type
class PaginationWindow(Generic[Item]):
    items: List[Item] = strawberry.field(
        description="The list of items in this pagination window."
    )

    total_items_count: int = strawberry.field(
        description="Total number of items in the filtered dataset."
    )
```

Note that `PaginationWindow` is generic - it can represent a slice of users, or
a slice of any other type of items that we might want to paginate.

`PaginationWindow` also contains `total_items_count`, which specifies how many
items there are in total in the filtered dataset, so that the client knows what
the highest offset value can be.

Let's define the query:

```python
@strawberry.type
class Query:
    @strawberry.field(description="Get a list of users.")
    def users(
        self,
        order_by: str,
        limit: int,
        offset: int = 0,
        name: str | None = None,
        occupation: str | None = None,
    ) -> PaginationWindow[User]:
        filters = {}

        if name:
            filters["name"] = name

        if occupation:
            filters["occupation"] = occupation

        return get_pagination_window(
            dataset=user_data,
            ItemType=User,
            order_by=order_by,
            limit=limit,
            offset=offset,
            filters=filters,
        )


schema = strawberry.Schema(query=Query)
```

Now we'll define a mock dataset and implement the `get_pagination_window`
function, which is used by the `users` query.

For the sake of simplicity, our dataset will be an in-memory list containing
four users:

```python
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
```

Here's the implementation of the `get_pagination_window` function. Note that it
is generic and should work for all item types, not only for the `User` type.

```python
def get_pagination_window(
    dataset: List[GenericType],
    ItemType: type,
    order_by: str,
    limit: int,
    offset: int = 0,
    filters: dict[str, str] = {},
) -> PaginationWindow:
    """
    Get one pagination window on the given dataset for the given limit
    and offset, ordered by the given attribute and filtered using the
    given filters
    """

    if limit <= 0 or limit > 100:
        raise Exception(f"limit ({limit}) must be between 0-100")

    if filters:
        dataset = list(filter(lambda x: matches(x, filters), dataset))

    dataset.sort(key=lambda x: x[order_by])

    if offset != 0 and not 0 <= offset < len(dataset):
        raise Exception(f"offset ({offset}) is out of range " f"(0-{len(dataset) - 1})")

    total_items_count = len(dataset)

    items = dataset[offset : offset + limit]

    items = [ItemType.from_row(x) for x in items]

    return PaginationWindow(items=items, total_items_count=total_items_count)


def matches(item, filters):
    """
    Test whether the item matches the given filters.
    This demo only supports filtering by string fields.
    """

    for attr_name, val in filters.items():
        if val not in item[attr_name]:
            return False
    return True
```

The above code first filters the dataset according to the given filters, then
sorts the dataset according to the given `order_by` field.

It then calculates `total_items_count` (this must be done after filtering), and
then slices the relevant items according to `offset` and `limit`.

Finally, it converts the items to the given strawberry type, and returns a
`PaginationWindow` containing these items, as well as the `total_items_count`.

In a real project, you would probably replace this with code that fetches from a
database using `offset` and `limit`.

<Tip>

If you're using Strawberry with the Django web framework, you might want to make
use of the Django pagination API. You can check it out
[here](https://docs.djangoproject.com/en/4.0/topics/pagination/).

</Tip>

## Running the Query

Now, let us start the server and see offset-based pagination in action!

```shell
strawberry server example:schema
```

You will get the following message:

```text
Running strawberry on http://0.0.0.0:8000/graphql 🍓
```

Go to [http://0.0.0.0:8000/graphql](http://0.0.0.0:8000/graphql) to open
**GraphiQL**, and run the following query to get first two users, ordered by
name:

```graphql
{
  users(orderBy: "name", offset: 0, limit: 2) {
    items {
      name
      age
      occupation
    }
    totalItemsCount
  }
}
```

The result should look like this:

```json
{
  "data": {
    "users": {
      "items": [
        {
          "name": "Eddie Brock",
          "age": 20,
          "occupation": "Journalist, The Eddie Brock Report"
        },
        {
          "name": "Harold Osborn",
          "age": 19,
          "occupation": "President, Oscorp Industries"
        }
      ],
      "totalItemsCount": 4
    }
  }
}
```

The result contains:

- `items` - A list of the users in this pagination window
- `totalItemsCount` - The total number of items in the filtered dataset. In this
  case, since no filter was given in the request, `totalItemsCount` is 4, which
  is equal to the total number of users in the in-memory dataset.

Get the next page of users by running the same query, after incrementing
`offset` by `limit`.

Repeat until `offset` reaches `totalItemsCount`.

## Running a Filtered Query

Let's run the query again, but this time we'll filter out some users based on
their occupation.

```graphql
{
  users(orderBy: "name", offset: 0, limit: 2, occupation: "ie") {
    items {
      name
      age
      occupation
    }
    totalItemsCount
  }
}
```

By supplying `occupation: "ie"` in the query, we are requesting only users whose
occupation contains the substring "ie".

This is the result:

```json
{
  "data": {
    "users": {
      "items": [
        {
          "name": "Eddie Brock",
          "age": 20,
          "occupation": "Journalist, The Eddie Brock Report"
        },
        {
          "name": "Harold Osborn",
          "age": 19,
          "occupation": "President, Oscorp Industries"
        }
      ],
      "totalItemsCount": 3
    }
  }
}
```

Note that `totalItemsCount` is now 3 and not 4, because only 3 users in total
match the filter.
