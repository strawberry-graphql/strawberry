---
release type: minor
social_messages:
  x: >-
    {project_name} {version} is out! This release adds a schema breaking-change helper and CLI.
    🍓 https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. This release adds a schema breaking-change detection utility and CLI for SDL comparison.
---

This release adds a utility and CLI for detecting breaking GraphQL schema changes between SDL documents.

- `strawberry.utils.breaking_changes.find_breaking_changes_between_sdls` wraps graphql-core's `find_breaking_changes` for two SDL strings
- `strawberry breaking-changes` compares two `.graphql` files and exits 0 (no breaking changes), 1 (breaking changes found), or 2 (parse/read errors)
