Release type: minor

This release fixes that the subscription implementations did not respect when clients
specified a GraphQL subscription operation name when starting a subscription. Now client
sent messages like the following are handled as expected.

```json
{
  "type": "GQL_START",
  "id": "DEMO",
  "payload": {
    "query": "subscription Sub1 { sub1 } subscription Sub2 { sub2 }",
    "operationName": "Sub2"
  }
}
```
