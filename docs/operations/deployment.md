---
title: Deployment
---

# Deployment

Before deploying your GraphQL app to production you should disable GraphiQL and Introspection.

## Why are they bad?
1. They can reveal sensitive information

2. They make it easier for malicious actors to reverse engineer your GraphQL API

[See more on this topic](https://www.apollographql.com/blog/graphql/security/why-you-should-disable-graphql-introspection-in-production/)

## How to disable

### GraphiQL
GraphiQL is useful during testing and development but should be disabled in production by default.

See the Strawberry documentation for the integration you are using for more information on how to turn it off.

### Introspection
Introspection should primarily be used as a discovery and diagnostic tool for testing and development, and should be disabled in production by default.

You can disable introspection by [adding a validation rule extension](../extensions/add-validation-rules.md).
