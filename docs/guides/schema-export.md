---
title: Schema export
---

# Schema export

Sometimes IDE plugins and code generation tools require you to provide a GraphQL schema
definition.

Strawberry provides a command to export your schema definition.
The exported schema will be described in the GraphQL schema definition language (SDL).

You can export your schema using the following command:

    strawberry export-schema app:schema

where `schema` is the name of a Strawberry schema symbol and `app` the name of the
module containing the symbol.

In order to store the exported schema in a file, pipes or redirection can be utilized:

    strawberry export-schema app:schema > schema.graphql
