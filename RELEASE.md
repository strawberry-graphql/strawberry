Release type: minor

Starting with this release, the same JSON encoder is used to encode HTTP
responses and WebSocket messages.

This enables developers to override the `encode_json` method on their views to
customize the JSON encoder used by all web protocols.
