Release type: patch

This release extends the `strawberry server` command to allow the specification
of a schema symbol name within a module:

```sh
strawberry server mypackage.mymodule:myschema
```

The schema symbols name defaults to `schema` making this change backwards compatible.
