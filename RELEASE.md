Release type: minor

Starting with this release, clients using the legacy graphql-ws subprotocol will receive an error when they try to send binary data frames.
Before, binary data frames were silently ignored.

While vaguely defined in the protocol, the legacy graphql-ws subprotocol is generally understood to only support text data frames.
