Release type: patch

Improved execution performance by up to 10% by adding an optimized `is_awaitable` check with a fast path for common synchronous types (such as int, str, list, dict, etc.).

This optimization reduces overhead when processing large result sets containing mostly basic values by avoiding expensive awaitable checks for types that are known to never be awaitable.
