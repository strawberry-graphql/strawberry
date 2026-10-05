---
title: Invalid OneOf Input Field Error
---

# Invalid OneOf Input Field Error

## Description

This error is raised when a field of a OneOf input type (`one_of=True`) is
required or has a default value. Clients set exactly one field of a OneOf input
type, so GraphQL requires all its fields to be nullable and without a default.
For example, both fields of this input have a default, so when a client sets
`email`, GraphQL fills in `null` for `name`, and the input gets two keys:

```python
import strawberry


@strawberry.input(one_of=True)
class SearchBy:
    name: str | None = None
    email: str | None = None
```

A required field, like `name: str`, would have to be set in every request, so
clients couldn't set another field instead.

## How to fix this error

Declare the fields with `strawberry.Maybe`, which makes them nullable and
without a default:

```python
import strawberry


@strawberry.input(one_of=True)
class SearchBy:
    name: strawberry.Maybe[str]
    email: strawberry.Maybe[str]
```
