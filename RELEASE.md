Release type: patch

Use typing.Annotated for unions so type checkers and IDEs correctly infer the type


Before
```python
Animal = strawberry.union("Animal", (Cat, Dog))
```

After
```python
from typing import Annotated, Union

Animal = Annotated[Union[Cat, Dog], strawberry.union("Animal")]
```
