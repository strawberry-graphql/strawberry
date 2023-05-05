---
title: Errors
---

# Errors in strawberry

Strawberry has built-in errors for when something goes wrong with the creation
and usage of the schema.

It also provides a custom exception handler for improving how errors are printed
and to make it easier to find the exception source, for example the following
code:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def hello_world(self):
        return "Hello there!"


schema = strawberry.Schema(query=Query)
```

will show the following exception on the command line:

```text

  error: Missing annotation for field `hello_world`

       @ demo.py:7

     6 |     @strawberry.field
  ❱  7 |     def hello_world(self):
                 ^^^^^^^^^^^ resolver missing annotation
     8 |         return "Hello there!"


  To fix this error you can add an annotation, like so `def hello_world(...) -> str:`

  Read more about this error on https://errors.strawberry.rocks/missing-return-annotation

```

These errors are only enabled when `rich` and `libcst` are installed. You can
install Strawberry with errors enabled by running:

```shell
pip install "strawberry-graphql[cli]"
```

If you want to disable the errors you can do so by setting the
`STRAWBERRY_DISABLE_RICH_ERRORS` environment variable to `1`.
