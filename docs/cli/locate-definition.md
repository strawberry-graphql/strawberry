---
title: Locate definition
---

# Locate definition

Strawberry provides a CLI command `strawberry locate-definition` that allows you
to find the source location of a definition within the schema.

You can provide either a model name or a model name and field name, e.g.:

```
strawberry locate-definition path.to.schema:schema ObjectName
```

```
strawberry locate-definition path.to.schema:schema ObjectName.fieldName
```

If found, the result will be printed to the console in the form of
`path/to/file.py:line:column`, for example: `src/models/user.py:45:12`.

## Using with VS Code's Relay extension

You can use this command with the go to definition feature of VS Code's Relay
extension (configured via the `relay.pathToLocateCommand` setting).

You can create a script to do this, for example:

```sh
# ./locate-definition.sh
strawberry locate-definition path.to.schema:schema "$2"
```

Then, you can set the `relay.pathToLocateCommand` setting to the path of the
script, e.g.:

```json
"relay.pathToLocateCommand": "./locate-definition.sh"
```

You can then use the go to definition feature to navigate to the definition of a
model or field.
