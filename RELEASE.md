Added support to pass connection_params as dictionary to GraphQLWebsocketCommunicator when testing [channels integration](https://strawberry.rocks/docs/integrations/channels#testing)


### sample code snippet


```
GraphQLWebsocketCommunicator(
    application=application,
    path="/graphql",
    connection_params={"username": "strawberry"}
)
```