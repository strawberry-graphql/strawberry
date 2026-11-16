---
release type: patch
---

This release fixes `ListConnection` pagination allowing clients to bypass
the `relay_max_results` limit and mishandling malformed cursors.

Passing only a `before` cursor (without `first`/`last`) no longer returns
every item before the cursor: the window is now capped at `max_results`,
anchored at the start of the window, consistent with how `after` and
`first` are handled. In addition, cursors encoding a negative or
non-integer offset now raise the same
`Argument 'before'/'after' contains a non-existing value.` error used for
cursors with an unknown prefix, instead of producing negative indexes or
leaking internal `ValueError`/`islice` errors.
