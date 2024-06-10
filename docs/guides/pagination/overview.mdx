---
title: Pagination - Overview
---

# Pagination

Whenever we deal with lists in GraphQL, we usually need to limit the number of
items returned. Surely, we don't want to send massive lists of items that take a
considerable toll on the server! The goal of this guide is to help you get going
fast with pagination!

## Pagination at a Glance

Let us take a look at some of the common ways pagination can be implemented
today!

### Offset-Based Pagination

This type of pagination is widely used, and it is similar to the syntax we use
when looking up database records.

Here, the client specifies:

- `limit`: The number of items to be obtained at a time, and
- `offset`: The number of items to be skipped from the beginning.

Implementing offset-based pagination with an SQL database is straightforward. We
use the `limit` and `offset` values given to query for the items.

Offset-based pagination also provides us the ability to skip ahead to any
offset, without first needing to get all the items before it.

Let us understand offset-based pagination better, with an example. Let us assume
that we want to request a list of users, two at a time, from a server. We start
by sending a request to the server, with the desired `limit` and `offset`
values.

```json
{
  "limit": 2,
  "offset": 0
}
```

<Note>

We are not sending GraphQL requests here, don't worry about the request format
for now! We are looking into pagination conceptually. We'll implement pagination
in GraphQL later!

</Note>

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
      "age": 20
    }
  ]
}
```

To get the next two users, we can send another request, incrementing `offset` by
the value of `limit`.

```json
{
  "limit": 2,
  "offset": 2
}
```

We can repeat this process, incrementing `offset` by the value of `limit`, until
we get an empty result.

#### Pagination Metadata

In the example above, the result contained no metadata, only the items at the
requested offset and limit.

It may be useful to add metadata to the result. For example, the metadata may
specify how many items there are in total, so that the client knows what the
greatest offset value can be.

```json
{
  "users": [
    ...
  ]
  "metadata": {
    "count": 25
  }
}
```

#### Using page_number Instead of offset

Instead of using `limit` and `offset` as the pagination parameters, it may be
more useful to use `page_number` and `page_size`.

In such a case, the metadata in the result can be `pages_count`. The client
starts the pagination at `page_number` 1, incrementing by 1 each time to get the
next page, and ending when `page_size` is reached.

This approach may be more in line with what a typical client actually needs when
paginating.

#### Limitations of Offset-Based Pagination

Offset-based pagination has a few limitations:

- It is not suitable for large datasets, because we need to access offset +
  limit number of items from the dataset, before discarding the offset and only
  returning the requested items.
- It doesn't work well in environments where records are frequently added or
  removed, because in such cases, the page window becomes inconsistent and
  unreliable. This may result in duplicate items or skipped items across pages.

However, it provides a quick way to get started, and works well with
small-medium datasets. When your dataset scales, you will need a reliable and
consistent way to handle pagination.

### Cursor based pagination

<Note>

Strawberry provides a cursor based pagination implementing the
[relay spec](https://relay.dev/docs/guides/graphql-server-specification/). You
can read more about it in the [relay](../relay) page.

</Note>

Cursor based pagination, also known as keyset pagination, works by returning a
pointer to a specific item in the dataset. On subsequent requests, the server
returns results after the given pointer. This method addresses the drawbacks of
using offset pagination, but does so by making certain trade offs:

- The cursor must be based on a unique, sequential identifier in the given
  source.
- There is no concept of the total number of pages or results in the dataset.
- The client can’t jump to a specific page.

Let us understand cursor based pagination better, with the example given below.
We want to request a list of users, 2 at a time, from the server. We don't know
the cursor initially, so we will assign it a null value.

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

The next cursor returned by the server can be used to get the next set of users
from the server.

```json
{
  "limit": 2,
  "cursor": "3"
}
```

This is an example of forward pagination, but pagination can be done backwards
too!

## Implementing pagination in GraphQL

Let us look at how we can implement pagination in GraphQL.

- [Implementing Offset Pagination](./offset-based.md)
- [Implementing Cursor Pagination](./cursor-based.md)
- [Implementing the Relay Connection Specification](./connections.md)
