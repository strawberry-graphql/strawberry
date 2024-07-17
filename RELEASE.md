Release type: minor

This release changes some of the internals of Strawberry, it shouldn't
be affecting most of the users, but since we have changed the structure
of the code you might need to update your imports.

Thankfully we also provide a codemod for this, you can run it with:

```bash
strawberry upgrade update-imports
```

This release also includes additional documentation to some of
the classes, methods and functions, this is in preparation for
having the API reference in the documentation ✨
