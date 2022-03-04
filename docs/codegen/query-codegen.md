---
title: Codegen
experimental: true
---

# Query codegen

Strawberry supports code generation for GraphQL queries.

<Note>

Schema codegen will be supported in future releases.

</Note>

Let's assume we have the following GraphQL schema built with Strawberry:

```python
from typing import List

import strawberry


@strawberry.type
class Post:
    id: strawberry.ID
    title: str


@strawberry.type
class User:
    id: strawberry.ID
    name: str
    email: str

    @strawberry.field
    def post(self) -> Post:
        return Post(id=self.id, title=f"Post for {self.name}")


@strawberry.type
class Query:
    @strawberry.field
    def user(self, info) -> User:
        return User(id=strawberry.ID("1"), name="John", email="abc@bac.com")

    @strawberry.field
    def all_users(self) -> List[User]:
        return [
            User(id=strawberry.ID("1"), name="John", email="abc@bac.com"),
        ]


schema = strawberry.Schema(query=Query)
```

and we want to generate types based on the following query:

```graphql
query MyQuery {
  user {
    post {
      title
    }
  }
}
```

With the following command:

```bash
strawberry codegen --schema schema.py --output-dir ./output -p python query.graphql
```

We'll get the following output inside `output/types.py`:

```python
class MyQueryResultUserPost:
    title: str

class MyQueryResultUser:
    post: MyQueryResultUserPost

class MyQueryResult:
    user: MyQueryResultUser
```

## Why is this useful?

Query code generation is usually used to generate types for clients using your
GraphQL APIs.

Tools like [GraphQL Codegen](https://www.graphql-code-generator.com/) exist in
order to create types and code for your clients. Strawberry's codegen feature
aims to address the similar problem without needing to install a separate tool.
