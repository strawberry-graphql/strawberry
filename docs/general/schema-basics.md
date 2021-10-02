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
  name: str = "Example ^[lol](aaa)"
  ^[lol](books: typing.List['Book'])
```

[^author]: example footnote
