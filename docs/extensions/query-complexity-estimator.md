---
title: Query Complexity Estimator
summary: Add a validator to estimate the complexity of GraphQL operations.
tags: security
---

# `QueryComplexityEstimator`

Estimate the complexity of a query and attach its cost to the execution context.

This extension works by traversing through the query document and evaluating
each node's cost. If no field-specific override is provided, field costs are
estimated using `default_estimator`.

When the extension finishes estimating the complexity of the operations,
`callback` is called with a map of complexities of all operations and the
current execution context. This callback can be used for things such as a
token-bucket rate-limiter based on query complexity, a complexity logger, or for
storing the complexities in the current execution context so that it can used by
downstream resolvers.

Additionally, you can configure the extension also to add the complexity
dictionary to the response that gets sent to the client by setting
`response_key`.

## Usage example:

```python
from typing import Iterator

from graphql.error import GraphQLError

import strawberry
from strawberry.types import ExecutionContext
from strawberry.extensions import FieldComplexityEstimator, QueryComplexityEstimator


class MyEstimator(FieldComplexityEstimator):
    def estimate_complexity(
        self, child_complexities: Iterator[int], arguments: dict[str, Any]
    ) -> int:
        children_sum = sum(child_complexities)
        # scalar fields cost 1
        if children_sum == 0:
            return 1

        # non-list object fields cost the sum of their children
        if "page_size" not in arguments:
            return children_sum

        # paginated fields cost gets multiplied by page size
        return children_sum * arguments["page_size"]


# initialize your rate-limiter somehow
rate_limiter = ...


def my_callback(
    complexities: dict[str, int], execution_context: ExecutionContext
) -> None:
    # add complexities to execution context
    execution_context.context["complexities"] = complexities

    # apply a token-bucket rate-limiter
    total_cost = sum(complexities.values())
    bucket = rate_limiter.get_bucket_for_key(execution_context.context["user_id"])
    tokens_left = bucket.take_tokens(total_cost)
    if tokens_left <= 0:
        raise GraphQLError(
            "Rate-limit exhausted. Please wait for some time before trying again."
        )


schema = strawberry.Schema(
    Query,
    extensions=[
        QueryComplexityEstimator(
            default_estimator=MyEstimator(),
            callback=my_callback,
        ),
    ],
)
```

## API reference:

```python
class QueryComplexityEstimator(default_estimator, callback, response_key): ...
```

#### `default_estimator: Union[FieldComplexityEstimator, int]`

The default complexity estimator for fields that don't specify overrides. If
it's an integer, the default estimator will be a
`ConstantFieldComplexityEstimator` with the integer value.

#### `callback: Optional[Callable[[Dict[str, int], ExecutionContext], None]]`

Called each time validation runs. Receives a dictionary which is a map of the
complexity for each operation.

#### `response_key: Optional[str]`

If provided, this extension will add the calculated query complexities to the
response that gets sent to the client via `get_results()`. The resulting
complexities will be under the specified key.

```python
class FieldComplexityEstimator: ...
```

Estimate the complexity of a single field.

### `estimate_complexity(child_complexities, arguments) -> int:`

The implementation of the estimator

#### `child_complexities: Iterator[int]`

An iterator over the complexities of child fields, if they exist. This iterator
is lazy, meaning the complexity of each child will only be evaluated if `next()`
gets called on the iterator. As such, to avoid unnnecessary computation we
recommend only iterating over child complexities if you'll use them.

#### `arguments: Dict[str, Any]`

A dict that maps field arguments to their values.
