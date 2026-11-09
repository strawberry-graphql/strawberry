---
release type: patch
---

This release fixes `DataLoader` cancelling every caller of a cached key when
only one of them is cancelled.

Callers loading the same key used to share a single future, so cancelling one
of them (for example, graphql-core 3.3 cancelling the sibling resolvers of a
failing non-null field) made all the others raise `CancelledError`, which then
failed the whole request. graphql-core 3.2 didn't cancel those resolvers, it
let them finish and discarded their results, so the problem only showed up
after upgrading to graphql-core 3.3.

Each `load` call now gets its own future: cancelling it no longer affects other
callers, and the load of a key is cancelled only once all of its callers are.
As before, when all callers of a batch are cancelled, the batch load function
is skipped or cancelled.

This release also fixes later loads hanging forever after all the loads of a
batch were cancelled before the batch was dispatched.

Note that `loader.load(key)` called twice for the same cached key now returns
two different awaitables, both resolving to the same value. As each call has its
own awaitable, one that is never awaited (e.g. to prefetch a key) keeps the
load of its key going even if all other callers are cancelled, and if the load
fails, asyncio reports its exception as never retrieved, like for any other
future that is never awaited.
