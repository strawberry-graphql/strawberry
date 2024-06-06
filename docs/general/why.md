---
title: Why
---

# Why was Strawberry created?

Strawberry has been inspired by dataclasses[^1] and one of its goals is to
provide a great developer experience for both GraphQL beginners and advanced
users.

In addition to that we really want to create and foster a nice and welcoming
community with people using GraphQL in Python.

# Why should you use Strawberry?

<Note>

At the moment Strawberry is still in early development, so there's a chance of
things suddenly changing, but hopefully the public API is stable enough.

</Note>

Thanks to type hints and the decorator syntax inspired by dataclasses,
Strawberry provides a nice developer experience that will help writing better
GraphQL APIs while also helping finding bugs when using type checkers like MyPy.

Here's a basic example of a type and how it compares to the equivalent type in
GraphQL:

<CodeGrid>

```python
@strawberry.type
class User:
    id: strawberry.ID
    name: str
```

```graphql
type User {
  id: ID!
  name: String!
}
```

</CodeGrid>

As you can see the code is very similar to what you would write using the
GraphQL SDL. Thanks to this, we think Strawberry hits a perfect middle ground
between code first and schema first.

We also are going to provide useful features and integrations; for example we
provide support for Apollo Federation, File Uploads, Permissions and integration
with popular frameworks like Django, ASGI and Flask.

Finally, we try to fix bugs and provide help via GitHub or our
[Discord server](http://strawberry.rocks/discord), so if you have any issue feel
free to drop an issue or ask on Discord.

[^1]:
    More specifically by this
    [talk on dataclasses](https://www.youtube.com/watch?v=epKegvx_Jws)
