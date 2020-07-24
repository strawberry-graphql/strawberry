from functools import partial

from .field import field


# Mutations and subscriptions are field, we might want to separate things in the long run
# for example to provide better errors
mutation = field
subscription = partial(field, is_subscription=True)
