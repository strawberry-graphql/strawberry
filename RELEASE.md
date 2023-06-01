Release type: patch

In this release codegen no longer chokes on queries that use a fragment.

There is one significant limitation at the present.  When a fragment is included via the spread operator in an object, it must be the only field present.  Attempts to include more fields will result in a ``ValueError``.

However, there are some real benefits.  When a fragment is included in multiple places in the query, only a single class will be made to represent that fragment:

```
fragment Point on Bar {
   id
   x
   y
}

query GetPoints {
  circlePoints {
    ...Point
  }
  squarePoints {
    ...Point
  }
}
```

Might generate the following types

```py
class Point:
    id: str
    x: float
    y: float

class GetPointsResult:
    circle_points: List[Point]
    square_points: List[Point]
```

The previous behavior would generate duplicate classes for for the `GetPointsCirclePoints` and `GetPointsSquarePoints` even though they are really identical classes.
