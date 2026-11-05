---
release type: patch
---

This release fixes a bug where completing one GraphQL subscription could
silently stop delivery for sibling subscriptions on the same connection that
share a Channels group.

`listen_to_channel` now ref-counts group membership, so a group is only
discarded once every subscription sharing it has finished, concurrent joins
and leaves of the same group can't race each other, and a failed join no
longer leaves a stale group reference behind.
