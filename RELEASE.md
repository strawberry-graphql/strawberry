Release type: patch

Fix `AssertionError` caused by the `DatadogTracingExtension` whenever the query is unavailable.

The bug in question was reported by issue [#3150](https://github.com/strawberry-graphql/strawberry/issues/3150).
The datadog extension would throw an `AssertionError` whenever there was no query available. This could happen if,
for example, a user POSTed something to `/graphql` with a JSON that doesn't contain a `query` field as per the
GraphQL spec.

The fix consists of adding `invalid` to the `operation_type` tag, and also adding `invalid` to the resource name.
It also makes it easier to look for logs of users making invalid queries by searching for `invalid` in Datadog.
