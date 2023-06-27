Release type: patch

The `graphql-transport-ws` protocol allows for subscriptions to error during execution without terminating
the subscription.  Non-fatal errors produced by subscriptions now produce `Next` messages containing
an `ExecutionResult` with an `error` field and don't necessarily terminate the subscription.
This is in accordance to the behaviour of Apollo server.
