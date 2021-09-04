---
title: Testing
---

# Testing

The GraphiQL playground integrated with Strawberry available at
[http://localhost:8000/graphql](http://localhost:8000/graphql) can be a good place to
start testing your queries and mutations. But at some point, while you are developing
your application (or even before if you are practising TDD), you may want to write down
also some automatic tests.

We can use the Strawberry's `schema` to run our first test:

```
def test_query():
    query = """query($title: String!){
            books(title: $title){
                title
                author
            }
        }
    """

    resp = schema.execute_sync(
        query,
        variable_values={"title": "The Great Gatsby"},
    )

    assert resp.errors is None
    assert resp.data["books"] == [
        {
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
        }
    ]
```

Since Strawberry supports async it goes without saying that tests can also be runned with async:

```
@pytest.mark.asyncio
async def test_query_async():
    ...

    resp = await schema.execute(query, variable_values={"title": "The Great Gatsby"},
    )

    ...
```
