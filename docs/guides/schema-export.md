---
title: Schema export
---

# Schema export

Sometimes IDE plugins and code generation tools require you to provide a GraphQL
schema definition.

Strawberry provides a command to export your schema definition. The exported
schema will be described in the GraphQL schema definition language (SDL).

To use the command line tools, you have to ensure Strawberry was installed with
`strawberry-graphql[cli]`.

You can export your schema using the following command:

```bash
strawberry export-schema package.module:schema
```

where `schema` is the name of a Strawberry schema symbol and `package.module` is
the qualified name of the module containing the symbol. The symbol name defaults
to `schema` if not specified.

In order to store the exported schema in a file, pipes or redirection can be
utilized:

```bash
strawberry export-schema package.module:schema > schema.graphql
```

Alternatively, the `--output` option can be used:

```bash
strawberry export-schema package.module:schema --output schema.graphql
```
