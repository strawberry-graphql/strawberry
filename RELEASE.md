---
release type: patch
---

This release fixes validation of fragment spreads in `QueryDepthLimiter` and
`MaxAliasesLimiter`.

`QueryDepthLimiter` now tracks visited fragments while calculating operation depth,
preventing circular fragment references from causing unbounded recursion.

`MaxAliasesLimiter` now expands fragment spreads when counting aliases, so aliases
declared inside fragments are counted each time the fragment is used.
