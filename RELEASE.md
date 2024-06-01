Release type: minor

This release separates the `relay.ListConnection` logic that calculates the
slice of the nodes into a separate function.

This allows for easier reuse of that logic for other places/libraries.

The new function lives in the `strawberry.relay.utils` and can be used by
calling `SliceMetadata.from_arguments`.

This has no implications to end users.
