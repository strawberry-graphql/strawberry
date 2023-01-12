---
title: Pagination
---

# Pagination

APIs commonly use pagination to efficiently return a portion of a result instead
of every single item, which can have inefficient performance.

The GraphQL spec [recommends cursor-based pagination](https://graphql.org/learn/pagination/)
and refers to [Relay's Connection Spec](https://relay.dev/graphql/connections.htm)
for specific implementation details.

Here we show a minimal example of how you can leverage Strawberry's generic Types
to build the types required to comply with the relay spec.

First, we'll implement a naive mock database. Name this file `db.py`:
```python
import base64
import typing


class DBBook:
    id: int
    title: str

    def __init__(self, id_: int, title: str):
        self.id = id_
        self.title = title


def encode(val: str) -> str:
    val_bytes = base64.b64encode(val.encode('ascii'))
    return val_bytes.decode('ascii')


def decode(val: str) -> str:
    val_bytes = base64.b64decode(val.encode('ascii'))
    return val_bytes.decode('ascii')


BOOKS_COUNT = 20

# The mock DB, ordered by title.
books = [DBBook(id_=i, title=f'Title {i}')
         for i in range(1, BOOKS_COUNT + 1)]


def build_book_cursor(book):
    """
    The book cursor must be based on the same "db column" that the result of
    get_books is ordered by.
    """
    return encode(book.title)


def get_books(limit: int, cursor: typing.Optional[str]) -> typing.List[DBBook]:
    """
    Return books from the mock db starting *after* the given cursor, limited to 
    the given number of books, ordered by title. The cursor must be an encoded 
    title, or None in order to start at the beginning.
    """
    if cursor is None:
        # start at the beginning
        return books[:limit]

    start_title = decode(cursor)
    found_idx = [idx for idx, book in enumerate(books)
                 if book.title == start_title]
    if len(found_idx) == 0:
        # cursor not found
        raise Exception(f'Cursor not found: {cursor}')

    # start *after*, not at, the given cursor
    start_idx = found_idx[0] + 1
    
    # limit how many books are returned
    end_idx = start_idx + limit
    return books[start_idx:end_idx]

```

Now, let's write the strawberry schema and query. Name this file `pagination.py`:

```python
import strawberry
import db
from typing import List, Generic, TypeVar, Optional

GenericType = TypeVar("GenericType")


@strawberry.type
class Connection(Generic[GenericType]):
    """Represents a paginated relationship between two entities

    This pattern is used when the relationship itself has attributes.
    In a Facebook-based domain example, a friendship between two people
    would be a connection that might have a `friendshipStartTime`
    """
    page_info: "PageInfo"
    edges: List["Edge[GenericType]"]


@strawberry.type
class PageInfo:
    """Pagination context to navigate objects with cursor-based pagination

    Instead of classic offset pagination via `page` and `limit` parameters,
    here we have a cursor of the last object and we fetch items starting from that one

    Read more at:
        - https://graphql.org/learn/pagination/#pagination-and-edges
        - https://relay.dev/graphql/connections.htm
    """
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]


@strawberry.type
class Edge(Generic[GenericType]):
    """An edge may contain additional information of the relationship. This is the trivial case"""
    node: GenericType
    cursor: str


@strawberry.type
class Book:
    id: strawberry.ID
    title: str

    @classmethod
    def from_db_model(cls, instance: db.DBBook):
        """Adapt this method with logic to map your orm instance to a strawberry decorated class"""
        return cls(id=instance.id, title=instance.title)


Cursor = str


def get_books(first: int, after: Optional[Cursor]) -> Connection[Book]:
    # get one extra book to check whether there is a next page
    books = db.get_books(first + 1, after)

    edges = [
        Edge(node=Book.from_db_model(book), cursor=db.build_book_cursor(book))
        for book in books[:first]
    ]

    return Connection(
        page_info=PageInfo(
            has_previous_page=after is not None,
            has_next_page=len(books) > first,
            start_cursor=edges[0].cursor if edges else None,
            end_cursor=edges[-1].cursor if edges else None,
        ),
        edges=edges
    )


@strawberry.type
class Query:
    books: Connection[Book] = strawberry.field(resolver=get_books)


schema = strawberry.Schema(query=Query)
```

Run `strawberry server pagination`

Go to [http://0.0.0.0:8000/graphql](http://0.0.0.0:8000/graphql) to open **GraphiQL**,
and run the following query to get the first two books:

```
{
  books(first: 2, after: null) {
    pageInfo {
      hasPreviousPage
      hasNextPage
      startCursor
      endCursor
    }
    edges {
      node {
        id
        title
      }
      cursor
    }
  }	
}
```
The result should look like this: 
```
{
  "data": {
    "books": {
      "pageInfo": {
        "hasPreviousPage": false,
        "hasNextPage": true,
        "startCursor": "VGl0bGUgMQ==",
        "endCursor": "VGl0bGUgMg=="
      },
      "edges": [
        {
          "node": {
            "id": "1",
            "title": "Title 1"
          },
          "cursor": "VGl0bGUgMQ=="
        },
        {
          "node": {
            "id": "2",
            "title": "Title 2"
          },
          "cursor": "VGl0bGUgMg=="
        }
      ]
    }
  }
}
```
Note that `hasPreviousPage` is `false`, to indicate that this is the first page.

Get the next two books by running the same query, after changing `after` to be the 
value of `endCursor` received in the result (`"VGl0bGUgMg=="`). 

Repeat until `hasNextPage` is `false`.
