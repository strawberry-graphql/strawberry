---
release type: patch
---

This release fixes Strawberry's rich exception handler crashing with
`Error in sys.excepthook` when a Strawberry error is raised from a script run
directly, such as `python app.py`.

Python 3.13.15+, 3.14.7+ and 3.15 remove `__file__` from `__main__` before an
uncaught exception reaches `sys.excepthook`, so Strawberry couldn't find the
source of the error. Strawberry now also finds the source file via the module's
spec or loader, and shows the error with its source again.

Errors whose source file is outside the current working directory (for example
when running `python ../app.py`) are now shown with the file's absolute path,
instead of crashing the handler.

When the source can't be found at all (for example with `python -c` or in the
REPL), or rendering the error fails for any other reason, Strawberry now falls
back to the standard Python traceback.
