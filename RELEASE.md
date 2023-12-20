Release type: minor

Related to [#1707](https://github.com/strawberry-graphql/strawberry/issues/1707). This requires support for the underneath example in the curl command. See the [documentation here](https://www.apollographql.com/docs/apollo-server/performance/apq/#command-line-testing).

```bash
curl --get http://localhost:4000/graphql \
  --header 'content-type: application/json' \
  --data-urlencode 'extensions={"persistedQuery":{"version":2,"sha256Hash":"ecf4edb46db40b5132295c0291d62fb65d6759a9eedfa4d5d612dd5ec54a6b38"}}'
```
