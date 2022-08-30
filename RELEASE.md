Release type: patch

Fixing a bug in the subscription clean up when subscribing using the
 graphql-transport-ws protocol, which could occasionally cause a 'finally'
 statement within the task to not get run, leading to leaked resources.