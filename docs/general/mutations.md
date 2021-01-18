---
title: Mutations
---

# Mutations

As opposed to queries, mutation in GraphQL represent operation that cause writes
and/or side effects on the server. For example you can have a mutation that
sends an email or a mutation that creates a user.

Like queries mutation can return data, and they also accept parameters. Let's
implement a mutation that is supposed to send an email:

```python
import strawberry

# Reader, you can safely ignore Query in this example, it is required by
# strawberry.Schema so it is included here for completeness
@strawberry.type
class Query:
    @strawberry.field
    def hello() -> str:
        return "world"

@strawberry.type
class Mutation:
    @strawberry.mutation
    def send_email(self, email: str) -> bool:
        print(f'sending email to {email}')

        return True

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

Like queries, mutations are defined in a class that is then passed to the Schema
function. Here we create a `sendEmail` mutation that accept an email and returns
a boolean.

We would send the following GraphQL document to our server to execute the
mutation:

```graphql
sendEmail(email: "patrick@example.org")
```

This is basic example, normally you'd return more complex data and also accept
more complex data as input.
