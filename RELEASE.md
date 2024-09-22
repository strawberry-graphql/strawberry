Release type: minor

Starting with this release, WebSocket logic now lives in the base class shared between all HTTP integrations.
This makes the behaviour of WebSockets much more consistent between integrations and easier to maintain.
