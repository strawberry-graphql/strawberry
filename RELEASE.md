Release type: minor

Adds a new `on_subscription_result` hook to `SchemaExtension` that allows extensions to interact with and mutate the stream of events yielded by GraphQL subscriptions.

Previously, extensions were only triggered during the initial setup phase of a subscription, meaning transport layers (like WebSockets) bypassed them during the actual data streaming phase. This new hook solves this by executing right before each result is yielded to the client.

As part of this architectural update, the built-in `MaskErrors` extension has been updated to use this new hook, ensuring that sensitive exceptions are now correctly masked during WebSocket subscriptions.
