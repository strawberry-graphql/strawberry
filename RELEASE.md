Release type: patch

Fix Pydantic integration for Python 3.10.0 (which was missing the `kw_only`
parameter for `dataclasses.make_dataclass()`).
