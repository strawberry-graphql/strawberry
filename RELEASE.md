Release type: patch

Fix `strawberry.experimental.pydantic` to correctly handle nested `pydantic.v1`
models when running on Pydantic 2 (for example, `list[LegacyModel]` fields with
`all_fields=True`), and add a regression test for this case.
