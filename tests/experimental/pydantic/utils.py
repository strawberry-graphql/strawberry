import pytest

from strawberry.experimental.pydantic.v2_compat import IS_PYDANTIC_V2

needs_pydanticv2 = pytest.mark.skipif(not IS_PYDANTIC_V2, reason="requires Pydantic v2")
needs_pydanticv1 = pytest.mark.skipif(IS_PYDANTIC_V2, reason="requires Pydantic v1")