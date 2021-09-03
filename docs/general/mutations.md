---
title: Mutations
---

# Mutations

As opposed to queries, mutations in GraphQL represent operations that modify
server-side data and/or cause side effects on the server. For example, you can have a
mutation that creates a user or a mutation that sends an email. Like in queries, they
accept parameters, can return data or include nested fields as well.
This can be useful for fetching the new state of an object after an update.

Let's implement a mutation that is supposed to send an email:

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

The `sendEmail` mutation is a simplified example. However, in a real-world
application, we usually want to return more information if an error occurs.
Refer to [Dealing with errors](/docs/guides/errors#expected-errors) documentation to
learn how to return a union of types in mutation.
