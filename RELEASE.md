Release type: patch

This releases adds `selected_fields` on the `info` objects and it
allows to introspect the fields that have been selected in a GraphQL
operation.

This can become useful to run optimisation based on the queried fields.
