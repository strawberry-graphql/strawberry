---
title: SyncToAsync
summary: Enable support for using Django ORM in an async context.
tags: django,async
---

# `SyncToAsync`

This extension wraps all custom resolvers in the `sync_to_async` decorator from
`asgiref.sync` so that you can use the Django ORM in an async context.

Read more about using asynchronous support in Django: https://docs.djangoproject.com/en/3.2/topics/async/

## Usage example:

```python
import strawberry
from strawberry.extensions.sync_to_async import SyncToAsync

@strawberry.type
class Query:
    @strawberry.field
    def latest_book_name(self) -> str:
        # Use the Django ORM as you normally would
        return Book.objects.order_by("-created_at").first().name

schema = strawberry.Schema(
    Query,
    extensions=[
        SyncToAsync(),
    ]
)
result = await schema.execute("{ latestBookName }")  # Works!
```

## API reference:

```python
class SyncToAsync(thread_sensitive=True)
```

**`thread_sensitive: bool = True`**

Determine if the sync function will run in the same thread as all other
`thread_sensitive` functions.

Read more: https://docs.djangoproject.com/en/3.2/topics/async/#sync-to-async

## More examples:

<details>
  <summary>Using with Dataloader</summary>

```python
# schema.py
import strawberry
from strawberry.extensions.sync_to_async import SyncToAsync
from strawberry.django.dataloader import create_model_load_fn

# The Django Book model definition
from books.models import Book as BookModel

@strawberry.type
class Book:
    name: str
    author: str

    @classmethod
    def from_instance(cls, instance: BookModel):
        return cls(
            name=instance.name,
            author=instance.author,
        )

@strawberry.type
class Query:
    @strawberry.field
    async def get_book(self, info, id: int) -> Book:
        book_instance = await info.context["book_loader"].load(id)
        return Book.from_instance(book_instance)

schema = strawberry.Schema(
    Query,
    extensions=[
        SyncToAsync(),
    ]
)
```

```python
# urls.py
from strawberry.django.views import GraphQLView

# Create a custom Django view to inject the loader into context
class GraphQLView(BaseGraphQLView):
    def get_context(self, request, response):
        return {
            "request": request,
            "book_loader": Dataloader(load_fn=create_model_load_fn(BookModel)),
        }

urlpatterns = [
    path("graphql/", GraphQLView.as_view(schema=schema)),
]
```

</details>
