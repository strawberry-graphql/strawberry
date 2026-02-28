Release type: patch

Fix `from __future__ import annotations` breaking lazy types inside generic wrappers like `Optional[]`, `tuple[]`, `dict[]`, `Sequence[]`, etc. Previously only `Union[]`, `list[]`/`List[]`, and `Annotated[]` were handled during AST namespace resolution, causing `_eval_type` to fail when lazy types were nested inside other generic subscripts.
