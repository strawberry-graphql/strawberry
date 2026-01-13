---
title: Testing
---

# Testing

The GraphiQL playground integrated with Strawberry available at
[http://localhost:8000/graphql](http://localhost:8000/graphql) (if you run the
schema with `strawberry dev`) can be a good place to start testing your queries
and mutations. However, at some point, while you are developing your application
(or even before if you are practising TDD), you may want to create some
automated tests.

We can use the Strawberry `schema` object we defined in the
[Getting Started tutorial](../index.md#step-5-create-our-schema-and-run-it) to
run our first test: `test_sample_query.py`

```python
import unittest
import strawberry
import typing


@strawberry.type
class Book:
    title: str
    author: str


def get_books():
    return [
        Book(
            title="The Great Gatsby",
            author="F. Scott Fitzgerald",
        ),
    ]


@strawberry.type
class Query:
    books: typing.List[Book] = strawberry.field(resolver=get_books)


class TestQuery(unittest.TestCase):
    def setUp(self):
        self.schema = strawberry.Schema(Query)

    def test_sample_query(self):
        query = """
        query TestQuery {
            books {
                title
                author
            }
        }
        """
        result = self.schema.execute_sync(query)
        assert result.errors is None
        self.assertEqual(
            result.data["books"],
            [
                {
                    "title": "The Great Gatsby",
                    "author": "F. Scott Fitzgerald",
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
```

This `test_query` example:

1. can be run using `python -m unittest path/to/test_sample_query.py`
2. defines the query we will test against
3. executes the query and assigns the result to a `result` variable
4. asserts that the result is what we are expecting: nothing in `errors` and our
   desired book in `data`

## Testing Async

Since Strawberry supports async, tests can also be written to be async:

```python
@pytest.mark.asyncio
async def test_query_async():
    ...

    resp = await schema.execute(query, variable_values={"title": "The Great Gatsby"})

    ...
```

## Testing Mutations

We can also write a test for our [`addBook` Mutation](../general/mutations.md)
example:

```python
@pytest.mark.asyncio
async def test_mutation():
    mutation = """
        mutation TestMutation($title: String!, $author: String!) {
            addBook(title: $title, author: $author) {
                title
            }
        }
    """

    resp = await schema.execute(
        mutation,
        variable_values={
            "title": "The Little Prince",
            "author": "Antoine de Saint-Exupéry",
        },
    )

    assert resp.errors is None
    assert resp.data["addBook"] == {
        "title": "The Little Prince",
    }
```

## Testing Subscriptions

And finally, a test for our [`count` Subscription](../general/subscriptions.md):

```python
import asyncio
import pytest
import strawberry


@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 100) -> int:
        for i in range(target):
            yield i
            await asyncio.sleep(0.5)


@strawberry.type
class Query:
    @strawberry.field
    def hello() -> str:
        return "world"


schema = strawberry.Schema(query=Query, subscription=Subscription)


@pytest.mark.asyncio
async def test_subscription():
    query = """
    	subscription {
        	count(target: 3)
    	}
    """

    sub = await schema.subscribe(query)

    index = 0
    async for result in sub:
        assert not result.errors
        assert result.data == {"count": index}

        index += 1
```

As you can see testing Subscriptions is a bit more complicated because we want
to check the result of each individual result.
