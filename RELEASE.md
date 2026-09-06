---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Channels HTTP responses now respect custom
    encode_json overrides returning str or bytes.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out! This release fixes custom JSON encoding for
    Channels HTTP responses. Both synchronous and asynchronous consumers now
    respect encode_json overrides returning str or bytes.
---

This release fixes Channels HTTP responses bypassing custom `encode_json`
overrides.

Both `GraphQLHTTPConsumer` and `SyncGraphQLHTTPConsumer` now use the encoding hook
for single and batched JSON responses, including GraphQL errors. Bytes are sent
unchanged, while strings are encoded as UTF-8.
