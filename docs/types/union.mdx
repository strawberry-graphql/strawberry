---
title: Union types
---

# Union types

Union types are similar to [interfaces](/docs/types/interfaces) however, while
interfaces dictate fields that must be common to all implementations, unions do
not. Unions only represent a selection of allowed types and make no requirements
on those types. Here’s a union, expressed in
[GraphQL Schema Definition Language](https://graphql.org/learn/schema/#type-language)
(SDL):

```graphql
union MediaItem = Audio | Video | Image
```

Whenever we return a `MediaItem` in our schema, we might get an `Audio`, a
`Video` or an `Image`. Note that members of a union type need to be concrete
object types; you cannot create a union type out of interfaces, other unions or
scalars.

A good use case for unions would be on a search field. For example:

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
is part of the `MediaItem` union. So, for each member, we want to select
different fields depending on which kind of object that member is. We can do
that by using
[inline fragments](https://graphql.org/learn/queries/#inline-fragments).

## Defining unions

In Strawberry there are two ways to define a union:

You can use the `Union` type from the `typing` module which will autogenerate
the type name from the names of the union members:

<CodeGrid>

```python
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
```

```graphql
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

</CodeGrid>

Or if you need to specify a name or a description for a union you can use
Annotated with the `strawberry.union` function:

<CodeGrid>

```python
import strawberry

from typing import Union, Annotated


@strawberry.type
class Query:
    latest_media: Annotated[Union[Audio, Video, Image], strawberry.union("MediaItem")]
```

```graphql
union MediaItem = Audio | Video | Image

type Query {
  latest_media: MediaItem!
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

</CodeGrid>

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

## Single member union

Sometimes you might want to define a union with only one member. This is useful
for future proofing your schema, for example if you want to add more types to
the union in the future.

Python's `typing.Union` does not really support this use case, but using
Annotated and `strawberry.union` you can tell Strawberry that you want to define
a union with only one member:

<CodeGrid>

```python
import strawberry

from typing import Annotated


@strawberry.type
class Audio:
    duration: int


@strawberry.type
class Query:
    latest_media: Annotated[Audio, strawberry.union("MediaItem")]
```

```graphql
union MediaItem = Audio

type Query {
  latestMedia: MediaItem!
}
```

</CodeGrid>
