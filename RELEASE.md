Release type: patch

This release fixes an `AttributeError` that occurred when a fragment and an `OperationDefinitionNode` shared the same name, and the fragment appeared first in the document.

The following example will now work as expected:

```graphql
fragment UserAgent on UserAgentType {
  id
}

query UserAgent {
  userAgent {
    ...UserAgent
  }
}