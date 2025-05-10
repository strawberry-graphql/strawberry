Release type: minor

This release changes GlobalIDs to ID in the GraphQL schema, now instead of
having `GlobalID` as type when using `relay.Node` you'll get `ID`.

The runtime behaviour is still the same.

If you need to use the previous behaviour you can use the following config:

```python
schema = strawberry.Schema(
    query=Query, config=StrawberryConfig(relay_use_legacy_global_id=True)
)
```
