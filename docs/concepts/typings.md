---
title: Type hints
---

# Type hints

Type hints are a modern feature of Python available since 3.5 whose existence is heavily influenced by the features of type-safe languages such as Rust. To learn more about type hints in Python, see [Real Python’s Type hinting walkthrough](https://realpython.com/lessons/type-hinting/).

When using Strawberry to build graphQL APIs, as was shown in [Schema basics](https://strawberry.rocks/docs/general/schema-basics), type hints are required within classes decorated by `@strawberry.type` & `@strawberry.input` and functions decorated by `@strawberry.field` & `strawberry.mutation`. These type hints are sourced as the keywords `str`, `int`, `float`, and from packages imported directly from the Python standard libraries `typing`, that has been available since Python 3.5, `datetime`, and `decimal`.

## Mapping to graphQL types

The complete mapping of the required type hints for the relevant graphQL types is as follows:

<<<<<<< HEAD
| GraphQL         | Python                        |
| --------------- | ----------------------------- |
| `ID`            | `strawberry.ID`               |
| `String`        | `str`                         |
| `Integer`       | `int`                         |
| `Float`         | `float`                       |
| `Decimal`       | `decimal.Decimal`             |
| `Array`, `[]`   | `typing.List` or `list`       |
| `Union`         | `typing.Union` or `|`         |
| `Nullable`      | `typing.Optional` or `None |` |
| `date`          | `datetime.date`               |
| `timetz`        | `datetime.time`               |
| `timestamptz`   | `datetime.datetime`           |

where `typing`, `datetime`, and `decimal` are all part of the Python standard library. There is also `typing.Dict` that possesses no mapping since it is the entire structure of the graphQL query itself that is a dictionary.

There are a few different ways in which these Python type hints can be used to express the required Strawberry graphQL type annotation.
- For versions of Python >= 3.10, it is possible to annotate an array of types with `list[Type]`. However, for all previous versions, `typing.List[Type]` must be used instead.
- The annotation `|` is shorthand for `typing.Union[]`, allowing either of `typing.Union[TypeA, TypeB]` or `TypeA | TypeB` interchangably.
- The annotation `typing.Optional[Type]` is shorthand for `typing.Union[None, Type]`, which is itself equivalent to `None | Type`.
=======
| GraphQL         | Python            |
| --------------- | ----------------- |
| `ID`            | `strawberry.ID`   |
| `String`        | `str`             |
| `Integer`       | `int`             |
| `Float`         | `float`           |
| `Array` or `[]` | `typing.List`     |
| `Union`         | `typing.Union`    |
| `Nullable`      | `typing.Optional` |
| `Date`          | `datetime.date`   |
| `Decimal`       | `decimal.Decimal` |

where `typing`, `datetime`, and `decimal` are all part of the Python standard library.

The usefulness of using `typing.List` instead of the keyword `list` is so that the types held in the list can be notated. A list of integers is notated as `typing.List[int]` and not as `list[int]`. The only effective equivalence that can be understood by the machine is that `typing.List[typing.Any]` is equivalent to `list`.

The `typing.Optional` hint signifies that the variable being hinted can be its type or `None`. As a result, `Optional[int]` is equivalent to `Union[None, int]`.
>>>>>>> 5614cb72c82a2b8550dfb0ca5b52e5d45e0724fd

## Example

A complete example of this, extending upon [Schema basics](https://strawberry.rocks/docs/general/schema-basics), might be the following:

```python
import datetime
import typing
import strawberry

BOOKS_LOOKUP = {
    'Frank Herbert': [{
        'title': 'Dune',
        'date_published': '1965-08-01',
        'price': '5.99',
        'isbn': 9780801950773
    }],
}

@strawberry.type
class Book:
    title: str
    author: 'Author'
    date_published: datetime.date
    price: decimal.Decimal
    isbn: Union[int, str] # could be 1234567890000 or '123-4-56-789000-0'

def get_books_by_author(root: 'Author') -> typing.List['Book']:
    # error will be thrown in here if a book in BOOKS_LOOKUP is missing a field
    # since none of the types of Book are optional
    stored_books: typing.List[typing.Dict[str, str | int]] = BOOKS_LOOKUP[root.name]
    return [Book(
        title = book.get('title'),
        date_published = book.get('date_published'),
        price = book.get('price'),
        isbn = book.get('isbn')
    ) for book in stored_books]

@strawberry.type
class Author:
    name: str
    books: typing.List['Book'] = strawberry.field(resolver=get_books_by_author)

@strawberry.type
class Group:
    name: Optional[str] # groups of authors don't necessarily have names
    authors: typing.List['Author']
    
    @strawberry.field
    def books(self) -> typing.List['Book']:
        books = []
        for author in self.authors:
            books += get_books_by_author(author)
        return books

```
- `self` within a resolver's definition, whether decorated as `@strawberry.field` or `@strawberry.mutation`, never needs a type hint because it can be inferred.
- `Optional` is the way to tell Strawberry that a field is nullable. Without it, every field is assumed to be non-null. This is in contrast to graphene wherein every field is assumed nullable unless `required=True` is supplied.
- Type hinting doesn't stop at being a requirement for Strawberry to function, it is also immensely helpful for collaborating developers. By specifying the type of `stored_books` in `get_books_by_author`, an IDE equipped with PyLance will be able to infer that `book` within the list comprehension is a dictionary and so will understand that `.get()` is a method function of the `dict` class. This helps the readability and maintainability of written code.

## Motivation

<<<<<<< HEAD
Python, much like Javascript and Ruby, is a _dynamically typed_ language that allows for high-level programming where the fundamental types of variables, e.g. integers, arrays, hash-maps, _etc._, are understood by the machine at _runtime_ through Just-in-Time compilation.

Yet, much like the low-level languages of C, Java, and Rust, the graphQL query language is _statically typed_ since the data types defined by the schema must be known prior to compiling the API code in order to define a definite schema to query against.

In the low-level _statically typed_ languages mentioned above, every function must have the types of both their arguments and returns explicitly declared so that the compiler can interpret their behaviours correctly and ensure type safety and consistency.

Strawberry takes inspiration from these languages by requiring that all of its types, fields, resolvers, and mutations declare the types of their arguments and returns. Through this, the schema is generated in a standard and efficient way that aligns with the style-direction of Python and programming as a whole.
=======
Python, much like Javascript and Ruby, is a _dynamically typed_ language that allows for high-level programming where the fundamental types of variables, e.g. integers, arrays, hash-maps, etc., are understood by the machine at _runtime_ through Just-in-Time compilation.

Yet, much like the low-level languages of C, Java, and Rust, the graphQL query language is _statically typed_ since the data types defined by the schema must be known prior to running the API in order to define a definite schema to query against.

In the low-level _statically typed_ languages in the above, every function must have the types of both their arguments and returns explicitly declared so that the compiler can interpret their behaviours correctly and ensure type safety and consistency.

Strawberry takes inspiration from these languages by requiring that all Strawberry types, fields, resolvers, and mutations declare the types of their arguments and returns. Through this, the schema is generated in a standard and efficient way that aligns with the style-direction of Python and programming as a whole.
>>>>>>> 5614cb72c82a2b8550dfb0ca5b52e5d45e0724fd
