---
release type: patch
---

This release fixes `strawberry codegen` crashing with a bare `StopIteration` when a
fragment spreads another fragment that is defined later in the document.

GraphQL doesn't care about the order fragments are defined in, and now neither does
codegen: fragments are processed after the fragments they spread, so both orders
generate the same code.
