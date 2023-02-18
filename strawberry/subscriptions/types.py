from typing import AsyncGenerator, TypeVar

__all__ = ["SubscriptionResult"]

T = TypeVar("T")

# Simple wrapper for Result type of GraphQL Subscription.
# Same as AsyncGenerator[T, None]
SubscriptionResult = AsyncGenerator[T, None]
