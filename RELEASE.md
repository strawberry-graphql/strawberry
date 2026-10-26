---
release type: patch
---

This release fixes query depth validation for documents that spread an undefined
fragment.

With `QueryDepthLimiter` enabled, Strawberry now reports the standard unknown
fragment error, including its source location, instead of an internal `KeyError`.
Depth checking still applies to the rest of the document.
