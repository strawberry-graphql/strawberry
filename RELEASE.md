Release type: patch

This release adds an optimization to `ListConnection` such that only queries with
`edges` or `pageInfo` in their selected fields triggers `resolve_edges`.

This change is particularly useful for the `strawberry-django` extension's
`ListConnectionWithTotalCount` and the only selected field is `totalCount`. An
extraneous SQL query is prevented with this optimization.
