Release type: minor

Nests the resolver under the correct span; prior to this change your span would have looked something like:

```
GraphQL Query
  GraphQL Parsing
  GraphQL Validation
  my_resolver
  my_span_of_interest #1
    my_sub_span_of_interest #2
```

After this change you'll have:

```
GraphQL Query
  GraphQL Parsing
  GraphQL Validation
  GraphQL Handling: my_resolver
    my_span_of_interest #1
      my_sub_span_of_interest #2
```
