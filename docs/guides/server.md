---
title: Builtin server
---

# Builtin server

Sometimes you need to quickly prototype an API and don’t really need to use a
framework like Flask or Django.

Strawberry’s built in server helps with this use case. It allows to quickly have
a development server by running the following command:

    strawberry server app

where `app` is the path to a file containing a Strawberry schema.

When running that command you should be able to see the GraphQL playground at
this url [http://localhost:8000/graphql](http://localhost:8000/graphql).
