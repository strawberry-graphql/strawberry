Release type: minor

Remove deprecated `graphiql` parameter from all HTTP integrations (ASGI, Flask, FastAPI, Quart, Sanic, Chalice, Django, Aiohttp, Channels, and Litestar), deprecated since [0.213.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.213.0).

### Migration guide

**Before (deprecated):**
```python
app = GraphQL(schema, graphiql=True)
```

**After:**
```python
app = GraphQL(schema, graphql_ide="graphiql")

# or to disable:
app = GraphQL(schema, graphql_ide=None)
```
