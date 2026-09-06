---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! DataLoader now spends less time allocating
    and enqueueing batch entries. https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out! We've reduced DataLoader's allocation and
    enqueue overhead while preserving batching, caching, and cancellation
    behavior. No application changes are needed.
---

This release fixes unnecessary allocation and enqueue overhead in DataLoader.

Batch entries now use slotted dataclasses and avoid runtime generic construction.
Batch selection also avoids repeated attribute lookups and length-method calls.
Existing batching, caching, priming, and cancellation behavior is preserved.
