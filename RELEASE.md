Release type: patch

This release improves the default logging format for errors to include more information about the errors. For example it will show were an error was originated in a request:

```
GraphQL request:2:5
1 | query {
2 |     example
  |     ^
3 | }
```
