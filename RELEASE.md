Release type: patch

Version 1.5.10 of GraphiQL disabled introspection for deprecated
arguments because it wasn't supported by all GraphQL server versions.
This PR enables it so that deprecated arguments show up again in
GraphiQL.
