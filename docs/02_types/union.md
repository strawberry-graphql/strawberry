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
    previewUrl
    resolution
  }
  ... on Image {
    thumbnailUrl
  }
}
```

Here, the `searchMedia` field returns `[MediaItem!]`, a list where each member
is part of the `MediaItem` union. Since union members share no fields,
selections are always made with [inline fragment](https://graphql.org/learn/queries/#inline-fragments).

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
    preview_url: str

@strawberry.type
class Image:
    thumbnail_url: str

@strawberry.type
class Query:
    search_media: Union[Audio, Video, Image]
---
union AudioVideoImage = Audio | Video | Image

type Query {
  searchMedia: AudioVideoImage!
}

type Audio {
  duration: Int!
}

type Image {
  thumbnailUrl: String!
}

type Video {
  previewUrl: String!
}
```

Or if you need to specify a name or a description for a union you can use the
`@strawberry.union` function:

```python+schema
import strawberry

MediaItem = strawberry.union("MediaItem", types=(Audio, Video, Image))

@strawberry.type
class Query:
    search_media: MediaItem
---
union MediaItem = Audio | Video | Image

type Query {
  searchMedia: AudioVideoImage!
}

type Audio {
  duration: Int!
}

type Image {
  thumbnailUrl: String!
}

type Video {
  previewUrl: String!
}
```
