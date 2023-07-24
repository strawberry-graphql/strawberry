import pytest

from strawberry.experimental.pydantic._compat import IS_PYDANTIC_V2

needs_pydantic_v2 = pytest.mark.skipif(
    not IS_PYDANTIC_V2, reason="requires Pydantic v2"
)
needs_pydantic_v1 = pytest.mark.skipif(IS_PYDANTIC_V2, reason="requires Pydantic v1")
