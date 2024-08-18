---
title: Accessing parent's data in resolvers
---

# Accessing parent's data in resolvers

It is quite common to want to be able to access the data from the field's parent
in a resolver. For example let's say that we want to define a `fullName` field
on our `User`. This would be our code:

<CodeGrid>

```python
import strawberry


@strawberry.type
class User:
    first_name: str
    last_name: str
    full_name: str
```

```graphql
type User {
  firstName: String!
  lastName: String!
  fullName: String!
}
```

</CodeGrid>

In this case `full_name` will need to access the `first_name` and `last_name`
fields, and depending on whether we define the resolver as a function or as a
method, we'll have a few options! Let's start with the defining a resolver as a
function.

## Accessing parent's data in function resolvers

```python
import strawberry


def get_full_name() -> str: ...


@strawberry.type
class User:
    first_name: str
    last_name: str
    full_name: str = strawberry.field(resolver=get_full_name)
```

Our resolver is a function with no arguments, in order to tell Strawberry to
pass us the parent of the field, we need to add a new argument with type
`strawberry.Parent[ParentType]`, like so:

```python
def get_full_name(parent: strawberry.Parent[User]) -> str:
    return f"{parent.first_name} {parent.last_name}"
```

`strawberry.Parent` tells Strawberry to pass the parent value of the field, in
this case it would be the `User`.

> **Note:** `strawberry.Parent` accepts a type argument, which will then be used
> by your type checker to check your code!

### Using root

Historically Strawberry only supported passing the parent value by adding a
parameter called `root`:

```python
def get_full_name(root: User) -> str:
    return f"{root.first_name} {root.last_name}"
```

This is still supported, but we recommend using `strawberry.Parent`, since it
follows Strawberry's philosophy of using type annotations. Also, with
`strawberry.Parent` your argument can have any name, for example this will still
work:

```python
def get_full_name(user: strawberry.Parent[User]) -> str:
    return f"{user.first_name} {user.last_name}"
```

## Accessing parent's data in a method resolver

Both options also work when defining a method resolver, so we can still use
`strawberry.Parent` in a resolver defined as a method:

```python
import strawberry


@strawberry.type
class User:
    first_name: str
    last_name: str

    @strawberry.field
    def full_name(self, parent: strawberry.Parent[User]) -> str:
        return f"{parent.first_name} {parent.last_name}"
```

But, here's where things get more interesting. If this was a pure Python class,
we would use `self` directly, right? Turns out that Strawberry also supports
this!

Let's update our resolver:

```python
import strawberry


@strawberry.type
class User:
    first_name: str
    last_name: str

    @strawberry.field
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
```

Much better, no? `self` on resolver methods is pretty convenient, and it works
like it should in Python, but there might be cases where it doesn't properly
follow Python's semantics. This is because under the hood resolvers are actually
called as if they were static methods by Strawberry.

Let's see a simplified version of what happens when you request the `full_name`
field, to do that we also need a field that allows to fetch a user:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        return User(first_name="Albert", last_name="Heijn")
```

When we do a query like this:

```graphql
{
  user {
    fullName
  }
}
```

We are pretty much asking to call the `user` function on the `Query` class, and
then call the `full_name` function on the `User` class, similar to this code:

```python
user = Query().user()

full_name = user.full_name()
```

While this might work for this case, it won't work in other cases, like when
returning a different type, for example when fetching the user from a database:

```python
import strawberry


@strawberry.type
class Query:
    @strawberry.field
    def user(self) -> User:
        # let's assume UserModel fetches data from the db and it
        # also has `first_name` and `last_name`
        user = UserModel.objects.first()

        return user
```

In this case our pseudo code would break, since `UserModel` doesn't have a
`full_name` function! But it does work when using Strawberry (provided that the
`UserModel` has both `first_name` and `last_name` fields).

As mentioned, this is because Strawberry class the resolvers as if they were
plain functions (not bound to the class), similar to this:

```python
# note, we are not instantiating the Query any more!
user = Query.user()  # note: this is a `UserModel` now

full_name = User.full_name(user)
```

You're probably thinking of `staticmethod`s and that's pretty much what we are
dealing with now! If you want to keep the resolver as a method on your class but
also want to remove some of the magic around `self`, you can use the
`@staticmethod` decorator in combination with `strawberry.Parent`:

```python
import strawberry


@strawberry.type
class User:
    first_name: str
    last_name: str

    @strawberry.field
    @staticmethod
    def full_name(parent: strawberry.Parent[User]) -> str:
        return f"{parent.first_name} {parent.last_name}"
```

Combining `@staticmethod` with `strawberry.Parent` is a good way to make sure
that your code is clear and that you are aware of what's happening under the
hood, and it will keep your linters and type checkers happy!
