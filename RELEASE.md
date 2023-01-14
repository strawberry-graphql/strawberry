Release type: minor

This change allows clients to define connectionParams when making Subscription requests similar to the way [Apollo-Server](https://www.apollographql.com/docs/apollo-server/data/subscriptions/#operation-context) does it.

With [Apollo-Client (React)](https://www.apollographql.com/docs/react/data/subscriptions/#5-authenticate-over-websocket-optional) as an example, define a Websocket Link:
```
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';

const wsLink = new GraphQLWsLink(createClient({
  url: 'ws://localhost:4000/subscriptions',
  connectionParams: {
    authToken: user.authToken,
  },
}));
```
and the JSON passed to `connectionParams` here will appear within Strawberry's context as the `connection_params` attribute when accessing `info.context` within a Subscription resolver.
