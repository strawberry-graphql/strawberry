---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes relay connections
    returning every item for `last: 0`. 🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes relay connections
    returning every item when queried with `last: 0`, so the result is now empty
    and the `relay_max_results` limit is respected.
---

This release fixes `ListConnection` returning every item when queried with
`last: 0` (without `before`).

The connection now returns no edges, with `hasPreviousPage` set to `true` when
there are items, as described by the Relay connection spec. Previously the
whole list was returned, ignoring `relay_max_results`. It also no longer reads
and resolves the whole source to answer such a query, only fetching a single
item to determine `hasPreviousPage`.
