---
title: Extension Name
summary: A summary of the extension.
tags: comma,separated,list,of,tags
---

# `ExtensionName`

This extension does ...

## Usage example:

```python
import strawberry
from strawberry.extensions import ExtensionName

schema = strawberry.Schema(
    Query,
    extensions=[
        ExtensionName(),
    ],
)
```

## API reference:

```python
class ExtensionName(an_argument=None): ...
```

#### `an_argument: Optional[str] = None`

Description of the argument.

## More examples:

<details>
  <summary>Using `an_argument`</summary>

```python
import strawberry
from strawberry.extensions import ValidationCache

schema = strawberry.Schema(
    Query,
    extensions=[
        ExtensionName(an_argument="something"),
    ],
)
```

</details>
