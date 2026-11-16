---
release type: patch
---

This release fixes `ListConnection` pagination with `before` and with cursors
that don't point to a valid offset.

`before` on its own (without `first` or `last`) now respects `max_results` and
`relay_max_results`. Previously a query like `users(before: $cursor)` returned
every item before the cursor, no matter how many there were.

Cursors with a negative or non-integer offset are now rejected with the same
`Argument 'before' contains a non-existing value.` (or `'after'`) error used for
cursors with the wrong prefix. Previously a negative `before` offset was used as
a negative Python index, so a `before` cursor encoding `arrayconnection:-5`
returned all but the last 4 items of the list, bypassing `max_results` too.
With iterators and generators these cursors failed with an internal `islice()`
error, and non-integer offsets failed with an `int()` parsing error.
