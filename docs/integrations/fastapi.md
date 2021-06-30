---
title: FastAPI
---

# FastAPI

Since FastAPI is ASGI compliant, you can plug the `GraphQL` ASGI app on a route:

```python
from fastapi import FastAPI
from strawberry.asgi import GraphQL

from api.schema import Schema

gqlapp = GraphQL(schema)

app = FastAPI()
app.add_route("/graphql", gqlapp)
```

For more information about strawberry ASGI refer to [asgi.md](asgi.md)

