---
release type: patch
---

This release fixes the Channels integration when using `cross-web` 0.6.0 or newer.

`cross-web` now requires request adapters to expose `path_params`, so Strawberry's
Channels HTTP adapters now read them from the Channels `url_route` scope.
