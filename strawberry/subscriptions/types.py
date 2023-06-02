from typing import AsyncGenerator, Type, TypeVar

__all__ = ["subscription_result"]

T = TypeVar("T")


def subscription_result(result_type: Type[T]) -> Type[AsyncGenerator[T, None]]:
    return AsyncGenerator[tuple([result_type, None])]  # type: ignore
