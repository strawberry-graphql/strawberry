Release type: patch

This release fixes a bug in the subscription implementations that prevented clients
from selecting one of multiple subscription operations from a query. Client sent
messages like the following one are now handled as expected.

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
