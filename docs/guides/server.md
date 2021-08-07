---
title: Builtin server
---

# Builtin server

Sometimes you need to quickly prototype an API and don’t really need to use a
framework like Flask or Django.

Strawberry’s built in server helps with this use case. It allows to quickly have
a development server by running the following command:

    strawberry server package.module:schema

where `schema` is the name of a Strawberry schema symbol and `package.module` is
the qualified name of the module containing the symbol. The symbol name defaults
to `schema` if not specified.

When running that command you should be able to see a GraphiQL playground at
this url [http://localhost:8000/graphql](http://localhost:8000/graphql).

## Automatic reloading

Strawberry's built in server automatically reloads when changes to the module
containing the `schema` are detected.
This way you can spend more time prototyping your API rather than restarting
development servers.
