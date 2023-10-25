Release type: patch

This release fixes an issue that prevented the `parser_cache` extension to be used in combination with
other extensions such as `MaxTokensLimiter`.

The following should work as expected now:

```python
schema = strawberry.Schema(
    query=Query, extensions=[MaxTokensLimiter(max_token_count=20), ParserCache()]
)
```
