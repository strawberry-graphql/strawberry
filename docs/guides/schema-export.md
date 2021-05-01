---
title: Schema export
---

# Schema export

Sometimes IDE plugins and code generation tools require you to provide a GraphQL schema
definition.

Strawberry provides a command to export your schema definition.
The exported schema will be described in the GraphQL schema definition language (SDL).

You can export your schema using the following command:

    strawberry export_schema app

where `app` is the path to a file containing a Strawberry schema.

In order to store the exported schema in a file, pipes can be utilized:

    strawberry export_schema app > schema.graphql
