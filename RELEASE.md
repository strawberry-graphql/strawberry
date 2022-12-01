Release type: minor

Added an error to be used when overriding GraphQLError in custom extensions and added a guide on how to use it.
Exposing GraphQLError from the strawberry namespace brings a better experience and will be useful in the future (when we move to something else).
