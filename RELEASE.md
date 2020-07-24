Release type: minor

This releases brings a much needed internal refactor of how we generate
GraphQL types from class definitions. Hopefully this will make easier to
extend Strawberry in future.

There are some internal breaking changes, so if you encounter any issue
let us know and well try to help with the migration.

In addition to the internal refactor we also fixed some bugs and improved
the public api for the schema class. Now you can run queries directly
on the schema by running `schema.execute`, `schema.execute_sync` and
`schema.subscribe` on your schema.
