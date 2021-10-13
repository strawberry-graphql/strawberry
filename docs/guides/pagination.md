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

### Cursor based pagination

Cursor-based pagination works by returning a pointer to a specific item in the dataset. On subsequent requests, the server returns results
after the given pointer. This method addresses the drawbacks of using offset pagination, but does so by making certain trade offs:

- The cursor must be based on a unique, sequential identifier in the given source.
- There is no concept of the total number of pages or results in the dataset.
- The client can’t jump to a specific page.

Let us understand cursor based pagination better, with an example.
Let us assume that we want to request a list of users from a server.

```json
{
    "limit": 10 # server returns 10 users at a time.
    "cursor": null # we don't know the cursor initially
}
```

The response from the server would be:

```json
{
    "users": [...],
    "next_cursor": "11",  # the user ID of the extra result.
}
```

Now, we can use the next cursor provided to get the next set of users from the server.

```json
{
    "limit": 10
    "cursor": "11" # we don't know the cursor initially
}
```

This is an example for forward pagination - pagination can be done backwards too!

-> **Note** The cursor used during pagination need not always be a number. It is an
-> opaque value that the client may use to page through the result set.

### Limit-offset pagination

documentation coming soon!

## Implementing pagination in GraphQL

Now that we know a few of the common ways to implement pagination, let us look at how we can implement them in GraphQL.

documentation coming soon!
