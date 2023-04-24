Release type: minor

This releases adds an extension for [PyInstrument](https://github.com/joerick/pyinstrument). It allows to instrument your server and find slow code paths.

You can use it like this:

```python
import strawberry
from strawberry.extensions import pyinstrument
schema = strawberry.Schema(
    Query,
    extensions=[
        pyinstrument.PyInstrument(report_path="pyinstrument.html"),
    ],
)
```
