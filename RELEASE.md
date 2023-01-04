Release type: minor

Support persisted query implementation via extensions.

View/controller implementations no longer return HTTP 400 if no query is present
in the request, but will still do if no query is found during execution. This
allows an extension to insert a query using the following template.

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
