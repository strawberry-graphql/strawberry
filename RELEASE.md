Release type: patch

Added pytest-xdist, for faster tests.

Before:
```shell
poetry run pytest

=============== 1637 passed, 23 skipped, 20 xfailed, 37 xpassed, 27 warnings in 115.97s (0:01:55)  ===============
```
After:
```shell
poetry run pytest -n auto

=============== 1637 passed, 23 skipped, 17 xfailed, 40 xpassed, 27 warnings in 53.34s ===============
```
