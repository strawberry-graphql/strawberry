Release type: minor

Calling `ChannelsConsumer.channel_listen` multiple times will now pass
along the messages being listened for to multiple callers, rather than
only one of the callers, which was the old behaviour.

This resolves an issue where creating multiple GraphQL subscriptions
using a single websocket connection could result in only one of those
subscriptions (in a non-deterministic order) being triggered if they
are listening for channel layer messages of the same type.
