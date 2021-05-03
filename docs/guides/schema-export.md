---
title: Schema export
---

# Schema export

Sometimes IDE plugins and code generation tools require you to provide a GraphQL schema
definition.

Strawberry provides a command to export your schema definition.
The exported schema will be described in the GraphQL schema definition language (SDL).

You can export your schema using the following command:

    strawberry export-schema package.module:schema

where `schema` is the name of a Strawberry schema symbol and `package.module` is
the qualified name of the module containing the symbol. The symbol name defaults
to `schema` if not specified.

In order to store the exported schema in a file, pipes or redirection can be utilized:

    strawberry export-schema package.module:schema > schema.graphql
