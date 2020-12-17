---
title: Union types
path: /docs/types/unions
---

# Union types

Union types are very similar to [interfaces](/docs/types/interfaces), but they don't have any common fields
between the types. Here’s a union, expressed in
[GraphQL Schema Definition Language](https://graphql.org/learn/schema/#type-language)
(SDL):

```graphql
union MediaItem = Audio | Video | Image
```

Whenever we return a `MediaItem` in our schema, we might get an `Audio`, a
`Video` or an `Image`. Note that members of a union type need to be concrete
object types; you cannot create a union type out of interfaces or other unions.

A good usecase for unions would be on a search field for example:

```graphql
searchMedia(term: "strawberry") {
  ... on Audio {
    duration
  }
  ... on Video {
    thumbnailUrl
  }
  ... on Image {
    src
  }
}
```

Here, the `searchMedia` field returns `[MediaItem!]!`, a list where each member
is part of the `MediaItem` union. Since union members share no fields,
selections are always made with [inline fragments](https://graphql.org/learn/queries/#inline-fragments).

## Defining unions

In Strawberry there are two ways to define a union:

You can use the use the `Union` type from the `typing` module:

```python+schema
from typing import Union
import strawberry

@strawberry.type
class Audio:
    duration: int

@strawberry.type
class Video:
    thumbnail_url: str

@strawberry.type
class Image:
    src: str

@strawberry.type
class Query:
    latest_media: Union[Audio, Video, Image]
---
union AudioVideoImage = Audio | Video | Image

type Query {
  latestMedia: AudioVideoImage!
}

type Audio {
  duration: Int!
}

type Video {
  thumbnailUrl: String!
}

type Image {
  src: String!
}
```

Or if you need to specify a name or a description for a union you can use the
`strawberry.union` function:

```python+schema
import strawberry

MediaItem = strawberry.union("MediaItem", types=(Audio, Video, Image))

@strawberry.type
class Query:
    latest_media: MediaItem
---
union MediaItem = Audio | Video | Image

type Query {
  latest_media: AudioVideoImage!
}

type Audio {
  duration: Int!
}

type Video {
  thumbnailUrl: String!
}

type Image {
  src: String!
}
```

> Note: Union types should never be instantiated directly.

## Resolving a union

When a field’s return type is a union, GraphQL needs to know what specific
object type to use for the return value. In the example above, each `MediaItem`
must be categorized as an `Audio`, `Image` or `Video` type. To do this you need
to always return an instance of an object type from your resolver:

```python
from typing import Union
import strawberry

@strawberry.type
class Query:
    @strawberry.field
    def latest_media(self) -> Union[Audio, Video, Image]:
        return Video(
            thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/hq720.jpg",
        )
```
