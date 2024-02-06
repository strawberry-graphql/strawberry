---
title: Codegen
experimental: true
---

# Query codegen

Strawberry supports code generation for GraphQL queries.

<Note>

Schema codegen will be supported in future releases. We are testing the query
codegen in order to come up with a nice API.

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

```shell
strawberry codegen --schema schema --output-dir ./output -p python query.graphql
```

We'll get the following output inside `output/query.py`:

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

## Plugin system

Strawberry's codegen supports plugins, in the example above for example, we are
using the `python` plugin. To pass more plugins to the codegen tool, you can use
the `-p` flag, for example:

```shell
strawberry codegen --schema schema --output-dir ./output -p python -p typescript query.graphql
```

the plugin can be specified as a python path.

### Custom plugins

The interface for plugins looks like this:

```python
from strawberry.codegen import CodegenPlugin, CodegenFile, CodegenResult
from strawberry.codegen.types import GraphQLType, GraphQLOperation


class QueryCodegenPlugin:
    def __init__(self, query: Path) -> None:
        """Initialize the plugin.

        The singular argument is the path to the file that is being processed by this plugin.
        """
        self.query = query

    def on_start(self) -> None: ...

    def on_end(self, result: CodegenResult) -> None: ...

    def generate_code(
        self, types: List[GraphQLType], operation: GraphQLOperation
    ) -> List[CodegenFile]:
        return []
```

- `on_start` is called before the codegen starts.
- `on_end` is called after the codegen ends and it receives the result of the
  codegen. You can use this to format code, or add licenses to files and so on.
- `generated_code` is called when the codegen starts and it receives the types
  and the operation. You cans use this to generate code for each type and
  operation.

### Console plugin

There is also a plugin that helps to orchestrate the codegen process and notify
the user about what the current codegen process is doing.

The interface for the ConsolePlugin looks like:

```python
class ConsolePlugin:
    def __init__(self, output_dir: Path):
        """Initialize the plugin and tell it where the output should be written."""
        ...

    def before_any_start(self) -> None:
        """This method is called before any plugins have been invoked or any queries have been processed."""
        ...

    def after_all_finished(self) -> None:
        """This method is called after the full code generation is complete.

        It can be used to report on all the things that have happened during the codegen.
        """
        ...

    def on_start(self, plugins: Iterable[QueryCodegenPlugin], query: Path) -> None:
        """This method is called before any of the individual plugins have been started."""
        ...

    def on_end(self, result: CodegenResult) -> None:
        """This method typically persists the results from a single query to the output directory."""
        ...
```
