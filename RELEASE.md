---
release type: patch
social_messages:
  x: >-
    {project_name} {version} is out! Smaller JSON responses with compact default
    encoding, preserving Unicode escaping and custom encoders.
    https://strawberry.rocks/release/{version}
  linkedin: >-
    {project_name} {version} is out. Strawberry's default JSON encoders now omit
    optional separator spaces to reduce response sizes. Unicode escaping,
    Django-specific serialization, and custom encoder overrides are preserved.
---

This release fixes unnecessary whitespace in responses produced by Strawberry's
shared default JSON encoders, reducing their size without changing decoded data.

The encoders now omit spaces after commas and colons. This also applies to
WebSocket messages and SSE/multipart JSON payloads that use these encoders;
protocol framing is unchanged. Unicode escaping, Django's `DjangoJSONEncoder`,
and custom `encode_json` overrides retain their existing behavior.

Channels' ordinary HTTP responses still use their separate serialization path
and are unaffected by this change.
