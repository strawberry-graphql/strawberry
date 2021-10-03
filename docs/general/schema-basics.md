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

<CodeNotes>
  <note id="author">This is the content of the footnote</note>
  <note id="lol">LOL</note>
</CodeNotes>
