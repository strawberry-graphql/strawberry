Release type: patch

This fixes a bug where codegen would choke on FragmentSpread nodes in the GraphQL during type collection.

e.g.:

```
fragment PartialBlogPost on BlogPost {
  title
}

query OperationName {
  interface {
    id
    ... on BlogPost {
      ...PartialBlogPost
    }
    ... on Image {
      url
    }
  }
}
```

The current version of the code generator is not able to handle the `...PartialBogPost` in this position because it assumes it can only find `Field` type nodes even though the spread should be legit.
