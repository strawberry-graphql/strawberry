---
title: Builtin server
---

# Builtin server

Sometimes you need to quickly prototype an API and don’t really need to use a
framework like Flask or Django.

Strawberry’s built in server helps with this use case. It allows to quickly have
a development server by running the following command:

```shell
strawberry server package.module:schema
```

where `schema` is the name of a Strawberry schema symbol and `package.module` is
the qualified name of the module containing the symbol. The symbol name defaults
to `schema` if not specified.

When running that command you should be able to see a GraphiQL playground at
this url [http://localhost:8000/graphql](http://localhost:8000/graphql).

## Automatic reloading

Strawberry's built in server automatically reloads when changes to the module
containing the `schema` are detected. This way you can spend more time
prototyping your API rather than restarting development servers.

## Disabling operation logging

By default Strawberry's built in server logs all operations that are executed.
This can be useful for debugging but can also be annoying if you are
prototyping.

To disable operation logging you can use the `--log-operations` configuration
flag:

```shell
strawberry server package.module:schema --log-operations False
```
