Release type: minor

This release adds support for updating (or adding) the query document inside an
extension's `on_request_start` method.

This can be useful for implementing persisted queries. The old behavior of
returning a 400 error if no query is present in the request is still supported.

Example usage:

```python
from strawberry.extensions import Extension

def get_doc_id(request) -> str:
    """Implement this to get the document ID using your framework's request object"""
    ...

def load_persisted_query(doc_id: str) -> str:
    """Implement this load a query by document ID. For example, from a database."""
    ...

class PersistedQuery(Extension):
    def on_request_start(self):
        request = self.execution_context.context.request

        doc_id = get_doc_id(request)

        self.execution_context.query = load_persisted_query(doc_id)
```
