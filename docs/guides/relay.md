---
title: Relay
---

# Relay Guide

## What is Relay?

The relay spec defines some interfaces that GraphQL servers can follow to allow
clients to interact with them in a more efficient way. The spec makes two
core assumptions about a GraphQL server:

1. It provides a mechanism for refetching an object
2. It provides a description of how to page through connections.

You can read more about the relay spec
[here](https://relay.dev/docs/en/graphql-server-specification).

### Relay implementation example

Suppose we have the following type:

```python
@strawberry.type
class Fruit:
    name: str
    weight: str
```

We want it to have a globally unique ID, a way to retrieve a paginated results
list of it and a way to refetch if if necessary. For that, we need to inherit it
from the `Node` interface and implement its abstract methods: `resolve_id`,
`resolve_node` and `resolve_nodes`.

```python
@strawberry.type
class Fruit(strawberry.relay.Node):
    code: strawberry.Private[int]
    name: str
    weight: float

    @classmethod
    def resolve_id(cls, root: Self, *, info: Optional[Info] = None):
        return root.code

    @classmethod
    def resolve_nodes(
        cls,
        *,
        info: Optional[Info] = None,
        node_ids: Optional[Iterable[str]] = None,
    ):
        if node_ids is not None:
            return [fruits[nid] for nid in node_ids]

        return list(fruits.values())

    @classmethod
    def resolve_node(
        cls,
        node_id: str,
        *,
        info: Optional[Info] = None,
        required: bool = False,
    ):
        obj = fruits.get(node_id, None)
        if required and obj is None:
            raise ValueError(f"No fruit by id {node_id}")

        return obj


# Assume we have a dict mapping the fruits code to the Fruit object itself
fruits: Dict[int, Fruit]
```

With that, our `Fruit` type know knows how to retrieve a `Fruit` instance given its
`id`, and also how to retrieve that `id`.

Now we can expose it in the schema for retrieval and pagination like:

```python
@strawberry.type
class Query:
    node: strawberry.relay.Node
    fruits: strawberry.relay.Connection[Fruit]
```

This will generate a schema like this:

```graphql
scalar GlobalID

interface Node {
  id: GlobalID!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Fruit implements Node {
  id: GlobalID!
  name: String!
  weight: Float!
}

type FruitEdge {
  cursor: String!
  node: Fruit!
}

type FruitConnection {
  pageInfo: PageInfo!
  edges: [FruitEdge!]!
  totalCount: Int
}

type Query {
  node(id: GlobalID!): Node!
  fruits(
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
  ): FruitConnection!
}
```

With only that we have a way to query `node` to retrieve any `Node` implemented
type in our schema (which includes our `Fruit` type), and also a way to retrieve
a list of fruits with pagination.

For example, to retrieve a single fruit given its unique ID:

```graphql
query {
  node(id: "<some id>") {
    id
    ... on Fruit {
      name
      weight
    }
  }
}
```

Or to retrieve the first 10 fruits available:

```graphql
query {
  fruitConnection(first: 10) {
    pageInfo {
      firstCursor
      endCursor
      hasNextPage
      hasPreviousPage
    }
    edges {
      # node here is the Fruit type
      node {
        id
        name
        weight
      }
    }
  }
}
```

### Custom connection pagination

The default `Connection` implementation uses a limit/offset approach to paginate
the results. This is a basic approach and might be enough for most use cases.

<Note>

`Connection` implementes the limit/offset by using slices. That means that you can
override what the slice does by customizing the `__getitem__` method of the object
returned by `resolve_nodes`.

For example, when working with `Django`, `resolve_nodes` can return a `QuerySet`,
meaning that the slice on it will translate to a `LIMIT`/`OFFSET` in the SQL
query, which will fetch only the data that is needed from the database.

Also note that if that object doesn't have a `__getitem__` attribute, it will
use `itertools.islice` to paginate it, meaning that when a generator is being
resolved it will only generate as much results as needed for the given pagination,
the worst case scenario being the last results needing to be returned.

</Note>

You may want to use a different approach to paginate your results. For example,
a cursor-based approach. For that you need to subclass the `Connection` type
and implement your own `from_nodes` method. For example, suppose that in our
exaple above, we want to use the fruit's weight as the cursor, we can implement
it like that:

```python
from strawberry.relay import to_base64


@strawberry.type
class CustomPaginationConnection(strawberry.relay.Connection[Fruit]):
    @classmethod
    def from_nodes(
        cls,
        nodes: Iterable[Fruit],
        *,
        info: Optional[Info] = None,
        total_count: Optional[int] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        first: Optional[int] = None,
        last: Optional[int] = None,
    ):
        # Note that this is a showcase implementation and is far from
        # being optimal performance wise
        edges_mapping = {
            to_base64("fruit_name", n.name): strawberry.relay.Edge(
                node=n,
                cursor=to_base64("fruit_name", n.name),
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
    fruits: CustomPaginationConnection
```

<Note>

In the example above we specialized the `FruitCustomPaginationConnection` by
inheriting it from `relay.Connection[Fruit]`. We could still keep it generic by
inheriting it from `relay.Connection[relay.NodeType]` and then specialize it
in when defining the field.

</Note>

### Custom connection resolver

We can define custom resolvers for the `Connection` as a way to pre-filter
the results. All that needs to be done is to decorate the resolver with
`@strawberry.relay.connection` and return an `Iterable` of that given
`Node` type in it. For example, suppose we want to return the pagination
of all fruits whose name starts with a given string:

```python
@strawberry.type
class Query:
    @strawberry.relay.connection
    def fruits_with_filter(
        self,
        info: Info,
        name_endswith: str,
    ) -> Iterable[Fruit]:
        for f in fruits.values():
            if f.name.endswith(name_endswith):
                yield f
```

This will generate a schema like this:

```graphql
type Query {
  fruitsWithFilter(
    nameEndswith: String!
    before: String = null
    after: String = null
    first: Int = null
    last: Int = null
  ): FruitConnection!
}
```

### The GlobalID scalar

The `GlobalID` scalar is a special object that contains all the info necessary to
identify and retrieve a given object that implements the `Node` interface.

It can for example be useful in a mutation, to receive and object and retrieve
it in its resolver. For example:

```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    def update_fruit_weight(
        self,
        info: Info,
        id: strawberry.relay.GlobalID,
        weight: float,
    ) -> Fruit:
        # resolve_node will return the Fruit object
        fruit = id.resolve_node(info, ensure_type=Fruit)
        fruit.weight = weight
        return fruit
```

In the example above, you can also access the type name directly with `id.type_name`,
the raw node ID with `id.id`, or even resolve the type itself with `id.resolve_type(info)`.
