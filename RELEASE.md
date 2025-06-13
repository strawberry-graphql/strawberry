Release type: patch

This release fixes that the Chalice HTTP view integration did not set
appropriate content-type headers for responses, as it's recommended by the
GraphQL over HTTP specification.
