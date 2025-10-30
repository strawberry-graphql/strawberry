---
title: Defer and Stream
---

# Defer and Stream

Strawberry provides experimental support for GraphQL's `@defer` and `@stream`
directives, which enable incremental delivery of response data. These directives
allow parts of a GraphQL response to be delivered as they become available,
rather than waiting for the entire response to be ready.

<Note>

This feature requires `graphql-core>=3.3.0a9` and is currently experimental. The
API and behavior may change in future releases.

**Important limitations:**

- Extensions (most importantly `MaskErrors`) are not fully supported yet.
  Extensions currently only process the initial result and do not handle
  incremental payloads delivered by `@defer` and `@stream`.
- This means error masking and other extension functionality will only apply to
  the initial response, not to deferred or streamed data.

</Note>

## Enabling Defer and Stream

To use `@defer` and `@stream` directives, you need to enable experimental
incremental execution in your schema configuration:

```python
import strawberry


@strawberry.type
class Query:
    # Your query fields here
    pass


schema = strawberry.Schema(
    query=Query, config={"enable_experimental_incremental_execution": True}
)
```

## Using @defer

The `@defer` directive allows you to mark parts of a query to be resolved
asynchronously. The initial response will include all non-deferred fields,
followed by incremental payloads containing the deferred data.

### Example

```python
import asyncio
import strawberry


@strawberry.type
class Author:
    id: strawberry.ID
    name: str
    bio: str


@strawberry.type
class Article:
    id: strawberry.ID
    title: str
    content: str

    @strawberry.field
    async def author(self) -> Author:
        # Simulate an expensive operation
        await asyncio.sleep(2)
        return Author(
            id=strawberry.ID("1"),
            name="Jane Doe",
            bio="A passionate writer and developer.",
        )


@strawberry.type
class Query:
    @strawberry.field
    async def article(self, id: strawberry.ID) -> Article:
        return Article(
            id=id,
            title="Introduction to GraphQL Defer",
            content="Learn how to use the @defer directive...",
        )
```

With this schema, you can query with `@defer`:

```graphql
query GetArticle {
  article(id: "123") {
    id
    title
    content
    ... on Article @defer {
      author {
        id
        name
        bio
      }
    }
  }
}
```

The response will be delivered incrementally:

```json
# Initial payload
{
  "data": {
    "article": {
      "id": "123",
      "title": "Introduction to GraphQL Defer",
      "content": "Learn how to use the @defer directive..."
    }
  },
  "hasNext": true
}

# Subsequent payload
{
  "incremental": [{
    "data": {
      "author": {
        "id": "1",
        "name": "Jane Doe",
        "bio": "A passionate writer and developer."
      }
    },
    "path": ["article"]
  }],
  "hasNext": false
}
```

## Using @stream with strawberry.Streamable

The `@stream` directive works with list fields and allows items to be delivered
as they become available. Strawberry provides a special `Streamable` type
annotation for fields that can be streamed.

### Example

```python
import asyncio
import strawberry
from typing import AsyncGenerator


@strawberry.type
class Comment:
    id: strawberry.ID
    content: str
    author_name: str


@strawberry.type
class BlogPost:
    id: strawberry.ID
    title: str

    @strawberry.field
    async def comments(self) -> strawberry.Streamable[Comment]:
        """Stream comments as they are fetched from the database."""
        for i in range(5):
            # Simulate fetching comments from a database
            await asyncio.sleep(0.5)
            yield Comment(
                id=strawberry.ID(f"comment-{i}"),
                content=f"This is comment number {i}",
                author_name=f"User {i}",
            )
```

Query with `@stream`:

```graphql
query GetBlogPost {
  blogPost(id: "456") {
    id
    title
    comments @stream(initialCount: 2) {
      id
      content
      authorName
    }
  }
}
```

The response will stream the comments:

```json
# Initial payload with first 2 comments
{
  "data": {
    "blogPost": {
      "id": "456",
      "title": "My Blog Post",
      "comments": [
        {
          "id": "comment-0",
          "content": "This is comment number 0",
          "authorName": "User 0"
        },
        {
          "id": "comment-1",
          "content": "This is comment number 1",
          "authorName": "User 1"
        }
      ]
    }
  },
  "hasNext": true
}

# Subsequent payloads for remaining comments
{
  "incremental": [{
    "items": [{
      "id": "comment-2",
      "content": "This is comment number 2",
      "authorName": "User 2"
    }],
    "path": ["blogPost", "comments", 2]
  }],
  "hasNext": true
}
# ... more incremental payloads
```
