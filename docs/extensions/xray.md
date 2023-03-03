---
title: XRayExtension
summary: Add X-Ray tracing to your GraphQL server.
tags: tracing
---

# `XRayExtension`

This extension adds support for tracing with AWS X-Ray.

<Note>

Make sure you have `aws-xray-sdk` installed before using this extension.

```
pip install aws-xray-sdk
```

</Note>

## Usage example:

```python
import strawberry
from strawberry.extensions.tracing import XRayExtension

schema = strawberry.Schema(
    Query,
    extensions=[
        XRayExtension,
    ],
)
```

<Note>

If you are not running in an Async context then you'll need to use the sync
version:

```python
import strawberry
from strawberry.extensions.tracing import XRayExtensionSync

schema = strawberry.Schema(
    Query,
    extensions=[
        XRayExtensionSync,
    ],
)
```

</Note>
