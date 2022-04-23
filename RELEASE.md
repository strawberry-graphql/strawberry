Release type: refactor

Changed the location of `UNSET` from `arguments.py` to `unset.py`. `UNSET` can now also be imported directly from `strawberry`. Deprecated the `is_unset` method in favor of the builtin `is` operator:

```python
from strawberry import UNSET
from strawberry.arguments import is_unset  # old

a = UNSET

assert a is UNSET  # new
assert is_unset(a)  # old
```
Further more a new subsection to the docs was added explaining this.
