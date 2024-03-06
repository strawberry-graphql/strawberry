Release type: minor

This release adds support to allow passing `connection_params` as dictionary to `GraphQLWebsocketCommunicator` class when testing [channels integration](https://strawberry.rocks/docs/integrations/channels#testing)


### Example


```python
GraphQLWebsocketCommunicator(
    application=application,
    path="/graphql",
    connection_params={"username": "strawberry"}
)
```
