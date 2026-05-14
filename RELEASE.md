Release type: minor

`relay.ListConnection` now supports an `offset` argument in addition to
`before`, `after`, `first`, and `last`. This lets clients skip a known number of
items without first converting that offset into a cursor, while keeping
`pageInfo` consistent with the skipped range.
