---
title: Type hints
---

# Type hints

Type hints are a modern feature of Python available since 3.5 whose existence is heavily influenced by the features of type-safe languages such as Rust. To learn more about type hints in Python, see [Real Python’s Type hinting walkthrough](https://realpython.com/lessons/type-hinting/).

When using Strawberry to build graphQL APIs, as was shown in [Schema basics](https://strawberry.rocks/docs/general/schema-basics), type hints are required within classes decorated by `@strawberry.type` & `@strawberry.input` and functions decorated by `@strawberry.field` & `strawberry.mutation`. These type hints are sourced as the keywords `str`, `int`, `float`, and from packages imported directly from the Python standard libraries `typing`, that has been available since Python 3.5, `datetime`, and `decimal`.

## Mapping to graphQL types

The complete mapping of the required type hints for the relevant graphQL types is as follows:

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

## Example

A complete example of this, extending upon [Schema basics](https://strawberry.rocks/docs/general/schema-basics), might be the following:
```python
import datetime
import typing
import strawberry

@strawberry.type
class Book:
    title: str
    author: 'Author'
    date_published: datetime.Date
    price: decimal.Decimal
    isbn_code: Union[int, str] # could be 1234567890000 or '123-4-56-789000-0'

@strawberry.type
class Author:
    name: str

    @strawberry.field
    async def books(self, info: strawberry.types.Info) -> typing.List['Book']:
        return await info.context['loaders'].load_books_by_author_name.load(self.name)

@strawberry.type
class Group:
    name: Optional[str] # groups of authors don't necessarily need a name
    authors: typing.List['Author']

    @strawberry.field
    async def books(self, info: strawberry.types.Info) -> typing.List['Book']:
        names = [author.name for author in self.authors]
        return await info.context['loaders'].load_books_by_author_names.load(names)
```

- `self` within a type's declaration never needs a type hint as it is inferred.
- See [Dataloaders](https://strawberry.rocks/docs/guides/dataloaders) for additional context on the `books` resolvers.
- `Optional` is the way to tell Strawberry that a field is nullable. Without it, every field is assumed to be non-null. This is in contrast to graphene wherein every field is assumed nullable unless `required=True` is supplied.

## Motivation

Python, much like Javascript and Ruby, is a *dynamically typed* language that allows for high-level programming where the fundamental types of variables, e.g. integers, arrays, hash-maps, etc., are understood by the machine at *runtime* through Just-in-Time compilation.

Yet, much like the low-level languages of C, Java, and Rust, the graphQL query language is *statically typed* since the data types defined by the schema must be known prior to running the API in order to define a definite schema to query against.

In the low-level *statically typed* languages in the above, every function must have the types of both their arguments and returns explicitly declared so that the compiler can interpret their behaviours correctly and ensure type safety and consistency.

Strawberry takes inspiration from these languages by requiring that all Strawberry types, fields, resolvers, and mutations declare the types of their arguments and returns. Through this, the schema is generated in a standard and efficient way that aligns with the style-direction of Python and programming as a whole.