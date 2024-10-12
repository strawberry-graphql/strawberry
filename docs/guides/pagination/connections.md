---
title: Pagination - Implementing the Connection Specification
---

# Implementing the Connection Specification

We naively implemented cursor based pagination in the
[previous tutorial](./cursor-based.md). To ensure a consistent implementation of
this pattern, the Relay project has a formal
[connection specification](https://relay.dev/graphql/connections.htm), and
strawberry provides a `Connection` generic type to implement it.

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

## Connection

A Connection represents a paginated relationship between two entities. This
pattern is used when the relationship itself has attributes. For example, we
might have a connection of users to represent a paginated list of users.

Strawberry provides a `relay.Connection` class, which contains the basics of
what you need to implement the specification, but don't implement any pagination
logic. To use it, all you need to do is to subclass it and implement its
abstract `resolve_connection` classmethod.

<Note>

For basic cases, Strawberry provides a `ListConnection` which already implements
a `resolve_connection`, which we are going to look in the next section.

</Note>

Lets look at an example for a connection of users:

```python
import strawberry
from strawberry.pagination import Connection, Edge, to_base64


@strawberry.type
class UserConnection(Connection[User]):
    @classmethod
    def resolve_connection(
        cls,
        nodes: Iterable[Fruit],
        *,
        info: Optional[Info] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
    ):
        # NOTE: This is a showcase implementation and is far from
        # being optimal performance wise
        edges_mapping = {
            to_base64("cursor-name", n.name): Edge(
                node=n,
                cursor=to_base64("cursor-name", n.name),
            )
            for n in sorted(nodes, key=lambda f: f.name)
        }
        edges = list(edges_mapping.values())
        first_edge = edges[0] if edges else None
        last_edge = edges[-1] if edges else None

        if after is not None:
            after_edge_idx = edges.index(edges_mapping[after])
            edges = [e for e in edges if edges.index(e) > after_edge_idx]

        if before is not None:
            before_edge_idx = edges.index(edges_mapping[before])
            edges = [e for e in edges if edges.index(e) < before_edge_idx]

        if first is not None:
            edges = edges[:first]

        if last is not None:
            edges = edges[-last:]

        return cls(
            edges=edges,
            page_info=strawberry.relay.PageInfo(
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
                has_previous_page=(
                    first_edge is not None and bool(edges) and edges[0] != first_edge
                ),
                has_next_page=(
                    last_edge is not None and bool(edges) and edges[-1] != last_edge
                ),
            ),
        )


@strawberry.type
class Query:
    @connection(UserConnection)
    def get_users(self) -> Iterable[User]:
        # This can be a database query, a generator, an async generator, etc
        return some_function_that_returns_users()
```

This would generate a schema like this:

```graphql
type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type User {
  id: ID!
  name: String!
  occupation: String!
  age: Int!
}

type UserEdge {
  cursor: String!
  node: User!
}

type UserConnection {
  pageInfo: PageInfo!
  edges: [UserEdge!]!
}

type Query {
  getUsers(
    first: Int = null
    last: Int = null
    before: String = null
    after: String = null
  ): UserConnection!
}
```

## ListConnection

Strawberry also provides `ListConnection`, a subclass of `Connection` that
implementes a limit/offset pagination algorithm by using slices.

If a limit/offset pagination is enough for your needs, the above example can be
simplified to use `ListConnection` to a basic resolver that returns one of:

- `List[<NodeType>]`
- `Iterator[<NodeType>]`
- `Iterable[<NodeType>]`
- `AsyncIterator[<NodeType>]`
- `AsyncIterable[<NodeType>]`
- `Generator[<NodeType>, Any, Any]`
- `AsyncGenerator[<NodeType>, Any]`

For example:

```python
import strawberry
from strawberry.pagination import Connection, Edge, to_base64


@strawberry.type
class Query:
    @connection(ListConnection[User])
    def get_users(self) -> Iterable[User]:
        # This can be a database query, a generator, an async generator, etc
        return some_function_that_returns_users()
```

Because the implementation will use a slice to paginate the data, that means you
can override what the slice does by customizing the `__getitem__` method of the
object returned by your nodes resolver.

For example, when working with `Django`, `resolve_nodes` can return a
`QuerySet`, meaning that the slice on it will translate to a `LIMIT`/`OFFSET` in
the SQL query, making it fetch only the data that is needed from the database.

Also note that if that object doesn't have a `__getitem__` attribute, it will
use `itertools.islice` to paginate it, meaning that when a generator is being
resolved it will only generate as much results as needed for the given
pagination, the worst case scenario being the last results needing to be
returned.

## Custom Connection Arguments

By default the connection will automatically insert some arguments for it to be
able to paginate the results. Those are:

- `before`: Returns the items in the list that come before the specified cursor
- `after`: Returns the items in the list that come after the " "specified cursor
- `first`: Returns the first n items from the list
- `last`: Returns the items in the list that come after the " "specified cursor

You can still define extra arguments to be used by your own resolver or custom
pagination logic, and those will be merged together. For example, suppose we
want to return the pagination of all users whose name starts with a given
string. We could do that like this:

```python
@strawberry.type
class Query:
    @connection(ListConnection[User])
    def get_users(self, name_starswith: str) -> Iterable[User]:
        return some_function_that_returns_users(name_startswith=name_startswith)
```

This will generate a `Query` like this:

```graphql
type Query {
  getUsers(
    nameStartswith: String!
    first: Int = null
    last: Int = null
    before: String = null
    after: String = null
  ): UserConnection!
}
```

## Converting the node to its proper type when resolving the connection

The connection expects that the resolver will return a list of objects that is a
subclass of its `NodeType`. But there may be situations where you are resolving
something that needs to be converted to the proper type, like an ORM model.

In this case you can subclass the `Connection`/`ListConnection` and provide a
custom `resolve_node` method to it, which by default returns the node as is. For
example:

```python
import strawberry
from strawberry.pagination import ListConnection, connection

from db.models import UserModel


@strawberry.type
class User:
    id: int
    name: str


@strawberry.type
class UserConnection(ListConnection[User]):
    @classmethod
    def resolve_node(cls, node: UserModel, *, info, **kwargs) -> User:
        return User(
            id=node.id,
            name=node.name,
        )


@strawberry.type
class Query:
    @connection(UserConnection)
    def get_users(self, info: strawberry.Info) -> Iterable[UserDB]:
        return UserDB.objects.all()
```

The main advantage of this approach instead of converting it inside the custom
resolver is that the `Connection` will paginate the `QuerySet` first, which in
case of Django will make sure that only the paginated results are fetched from
the database. After that, the `resolve_node` function will be called for each
result to retrieve the correct object for it.

We used Django for this example, but the same applies to any other other similar
use case, like SQLAlchemy, etc.

## Full working example

Here is a full working example of a connection of users which you can play with:

```python
from typing import Iterable
import strawberry
from strawberry.pagination import ListConnection, connection

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
    id: int
    name: str
    occupation: str
    age: int


@strawberry.type
class Query:
    @connection(ListConnection[User])
    def get_users(self) -> Iterable[User]:
        return [
            User(
                id=user["id"],
                name=user["name"],
                occupation=user["occupation"],
                age=user["age"],
            )
            for user in user_data
        ]


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
