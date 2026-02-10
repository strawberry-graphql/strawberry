Release type: minor

Remove deprecated Sanic-specific features: `json_encoder` parameter (deprecated since [0.147.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.147.0)), `json_dumps_params` parameter (deprecated since [0.147.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.147.0)), and context dot notation (deprecated since [0.146.0](https://github.com/strawberry-graphql/strawberry/releases/tag/0.146.0)).

### Migration guide

**json_encoder / json_dumps_params — Before (deprecated):**
```python
class MyView(GraphQLView):
    def __init__(self):
        super().__init__(json_encoder=MyEncoder, json_dumps_params={"indent": 2})
```

**After:**
```python
class MyView(GraphQLView):
    def encode_json(self, data):
        return json.dumps(data, cls=MyEncoder, indent=2)
```

**Context dot notation — Before (deprecated):**
```python
request = info.context.request
```

**After:**
```python
request = info.context["request"]
```
