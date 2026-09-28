---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! Strawberry now requires graphql-core 3.3,
    with @defer and @stream working on the final 3.3.0 release. 🍓
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Strawberry now requires graphql-core 3.3
    and drops support for graphql-core 3.2, with @defer and @stream working on
    the final graphql-core 3.3.0 release.
---

This release adds support for graphql-core 3.3.0 and drops support for
graphql-core 3.2 and the 3.3 pre-releases. See the
[breaking changes](https://strawberry.rocks/docs/breaking-changes/0.328.0) page
for upgrade notes.

It also fixes:

- `@defer` and `@stream` returning a single, non-incremental result on
  graphql-core 3.3.0.
- `@defer` and `@stream` in synchronous execution (`Schema.execute_sync` and
  the sync integrations) now return a clear error instead of crashing.
- Module-level lazy aliases (`Annotated["User", strawberry.lazy(...)]`) under
  `from __future__ import annotations` failing to resolve in some cases.
- `info.selected_fields` crashing on inline fragments without a type condition.
