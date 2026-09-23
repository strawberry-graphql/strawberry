---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! This release fixes validation caching when
    `QueryDepthLimiter` is enabled. https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release fixes validation caching when
    `QueryDepthLimiter` is enabled, so a repeated query is validated once
    instead of on every request.
---

This release fixes `ValidationCache` never hitting when `QueryDepthLimiter` is
also enabled.

`QueryDepthLimiter` built a new validator class on every request, which changed
the cache key each time. Identical limiter configuration now reuses one
validator class.
