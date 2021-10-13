---
title: Pagination
---

# Pagination

Whenever we deal with lists in GraphQL, we usually need to limit the number of items returned. Surely, we don't want to send massive lists of
items that take a considerable toll on the server! The goal of this guide is to help you get going fast with pagination!

## Pagination at a glance

We have always dealt with pagination in different situations. Let us take a look at some of the common ways pagination
can be implemented today!

-> **Note** The Relay specification already has an established pattern for pagination, via "connection" types. If you're interested,
-> you can check it out [here](https://relay.dev/graphql/connections.htm)!

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
      "name": "Norman Osborn",
      "occupation": "Founder, Oscorp Industries",
      "age": 42
    },
    {
      "name": "Peter Parker",
      "occupation": "Freelance Photographer, The Daily Bugle",
      "age": 16
    }
  ],
  "page_info": {
    "total": 200,
    "page": 1,
    "pages": 100
  }
}
```

Where total is the total number of items on all pages, page is the current page and pages is the total number of pages available.
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

Let us understand cursor based pagination better, with the sample example given below. We want to request a list of users, 2 at a time, from
a server. We don't know the cursor initially, so we will assign it a null value.

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
      "name": "Norman Osborn",
      "occupation": "Founder, Oscorp Industries",
      "age": 42
    },
    {
      "name": "Peter Parker",
      "occupation": "Freelance Photographer, The Daily Bugle",
      "age": 16
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

documentation coming soon!
