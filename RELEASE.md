Release type: patch

This release adds the ability to disable to_camel_case and capitalize_first:

```py
from strawberry.utils import str_converters

str_converters.auto_camelcase = False
str_converters.auto_capitalize = False
```
