---
title: Locate definition
---

# Locate definition

Strawberry provides a CLI command `strawberry locate-definition` that allows you to find the source location of a definition within the schema.

You can provide either a model name or a model name and field name, e.g.:

```
strawberry locate-definition path.to.schema:schema ObjectName
```

```
strawberry locate-definition path.to.schema:schema ObjectName.fieldName
```

If found, the result will be printed to the console in the form of `path/to/file.py:line:column`.
