Release type: patch

Adds a new CLI command `strawberry locate-definition` that allows you to find the source location of a definition in the schema.

```
strawberry locate-definition path.to.schema:schema ObjectName
```

```
strawberry locate-definition path.to.schema:schema ObjectName.fieldName
```

Results take the form of `path/to/file.py:line:column`.

This can be used, for example, with the go to definition feature of VS Code's Relay extension (configured via the `relay.pathToLocateCommand` setting).
