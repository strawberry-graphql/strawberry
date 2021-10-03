---
title: Test
toc: true
---

# Test

Code blocks now support:

# Highlighting words individually

```python highlight=strawberry,str
import strawberry

@strawberry.type
class X:
    name: str
```

# Highlighting lines

```python lines=1-4
import strawberry

@strawberry.type
class X:
    name: str
```

# Add notes to code comments

This is probably not implemented in the best way, but for now it works:

```python
import ^[info](strawberry)

@strawberry.type
class X:
    name: str
```

<CodeNotes id="info">Strawberry is a cool library</CodeNotes>
