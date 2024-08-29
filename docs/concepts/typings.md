---
title: Type hints
---

# Type hints

Type hints are a modern feature of Python available since 3.5 whose existence is
heavily influenced by the features of type-safe languages such as Rust. To learn
more about type hints in Python, see
[Real Python’s Type hinting walkthrough](https://realpython.com/lessons/type-hinting/).

When using Strawberry to build graphQL APIs, as was shown in
[Schema basics](https://strawberry.rocks/docs/general/schema-basics), type hints
are required within classes decorated by `@strawberry.type` &
`@strawberry.input` and functions decorated by `@strawberry.field` &
`strawberry.mutation`. These type hints are sourced as the keywords `str`,
`int`, `float`, and from packages imported directly from the Python standard
libraries `typing`, that has been available since Python 3.5, `datetime`, and
`decimal`.

## Mapping to graphQL types

The complete mapping of the required type hints for the relevant graphQL types
is as follows:

| GraphQL       | Python                         |
| ------------- | ------------------------------ |
| `ID`          | `strawberry.ID`                |
| `String`      | `str`                          |
| `Integer`     | `int`                          |
| `Float`       | `float`                        |
| `Decimal`     | `decimal.Decimal`              |
| `Array`, `[]` | `typing.List` or `list`        |
| `Union`       | `typing.Union` or `\|`         |
| `Nullable`    | `typing.Optional` or `None \|` |
| `Date`        | `datetime.date`                |
| `Datetime`    | `datetime.datetime`            |
| `Time`        | `datetime.time`                |

where `typing`, `datetime`, and `decimal` are all part of the Python standard
library. There is also `typing.Dict` that possesses no mapping since it is the
entire structure of the graphQL query itself that is a dictionary.

There are a few different ways in which these Python type hints can be used to
express the required Strawberry graphQL type annotation.

- For versions of Python >= 3.10, it is possible to annotate an array of types
  with `list[Type]`. However, for all previous versions, `typing.List[Type]`
  must be used instead.
- The annotation `|` is shorthand for `typing.Union[]`, allowing either of
  `typing.Union[TypeA, TypeB]` or `TypeA | TypeB` interchangably.
- The annotation `typing.Optional[Type]` is shorthand for
  `typing.Union[None, Type]`, which is itself equivalent to `None | Type`.

## Example

A complete example of this, extending upon
[Schema basics](https://strawberry.rocks/docs/general/schema-basics), might be
the following:

```python
import datetime
import decimal
from typing import List, Optional

import strawberry

BOOKS_LOOKUP = {
    "Frank Herbert": [
        {
            "title": "Dune",
            "date_published": "1965-08-01",
            "price": "5.99",
            "isbn": 9780801950773,
        }
    ],
}


@strawberry.type
class Book:
    title: str
    author: "Author"
    date_published: datetime.date
    price: decimal.Decimal
    isbn: str


def get_books_by_author(root: "Author") -> List["Book"]:
    stored_books = BOOKS_LOOKUP[root.name]

    return [
        Book(
            title=book.get("title"),
            author=root,
            date_published=book.get("date_published"),
            price=book.get("price"),
            isbn=book.get("isbn"),
        )
        for book in stored_books
    ]


@strawberry.type
class Author:
    name: str
    books: List[Book] = strawberry.field(resolver=get_books_by_author)


@strawberry.type
class Group:
    name: Optional[str]  # groups of authors don't necessarily have names
    authors: List[Author]

    @strawberry.field
    def books(self) -> List[Book]:
        books = []

        for author in self.authors:
            books += get_books_by_author(author)

        return books
```

- `self` within a resolver's definition, whether decorated as
  `@strawberry.field` or `@strawberry.mutation`, never needs a type hint because
  it can be inferred.
- `Optional` is the way to tell Strawberry that a field is nullable. Without it,
  every field is assumed to be non-null. This is in contrast to graphene wherein
  every field is assumed nullable unless `required=True` is supplied.
- Type hinting doesn't stop at being a requirement for Strawberry to function,
  it is also immensely helpful for collaborating developers. By specifying the
  type of `stored_books` in `get_books_by_author`, an IDE equipped with PyLance
  will be able to infer that `book` within the list comprehension is a
  dictionary and so will understand that `.get()` is a method function of the
  `dict` class. This helps the readability and maintainability of written code.

## Motivation

Python, much like Javascript and Ruby, is a _dynamically typed_ language that
allows for high-level programming where the fundamental types of variables, e.g.
integers, arrays, hash-maps, _etc._, are understood by the machine at _runtime_
through Just-in-Time compilation.

Yet, much like the low-level languages of C, Java, and Rust, the graphQL query
language is _statically typed_ since the data types defined by the schema must
be known prior to compiling the API code in order to define a definite schema to
query against.

In the low-level _statically typed_ languages mentioned above, every function
must have the types of both their arguments and returns explicitly declared so
that the compiler can interpret their behaviours correctly and ensure type
safety and consistency.

Strawberry takes inspiration from these languages by requiring that all of its
types, fields, resolvers, and mutations declare the types of their arguments and
returns. Through this, the schema is generated in a standard and efficient way
that aligns with the style-direction of Python and programming as a whole.
