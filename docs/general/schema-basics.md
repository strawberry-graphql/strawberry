---
title: Schema basics
---

```python
@strawberry.type
class Book:
  title: str
  author: ^[author](Author)

@strawberry.type
class Author:
  name: str = "Example"
  ^[lol](books: typing.List['Book'])
```

<CodeNotes id="author">
  This is the content of the footnote
</CodeNotes>

<CodeNotes id="lol">
  LOL
</CodeNotes>
