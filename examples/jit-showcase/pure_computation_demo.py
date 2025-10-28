#!/usr/bin/env python
"""Pure computation demonstration - shows dramatic JIT benefits.
This example uses pure synchronous field resolution with no I/O,
which is where JIT compilation provides the most dramatic speedups.
"""

import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import math
import statistics
import time

from graphql import execute_sync, parse

import strawberry
from strawberry.jit import CachedJITCompiler, compile_query


# Schema with LOTS of pure computed fields
@strawberry.type
class Metrics:
    value: float

    @strawberry.field
    def squared(self) -> float:
        return self.value**2

    @strawberry.field
    def cubed(self) -> float:
        return self.value**3

    @strawberry.field
    def sqrt(self) -> float:
        return math.sqrt(abs(self.value))

    @strawberry.field
    def log(self) -> float:
        return math.log(abs(self.value) + 1)

    @strawberry.field
    def sin(self) -> float:
        return math.sin(self.value)

    @strawberry.field
    def cos(self) -> float:
        return math.cos(self.value)

    @strawberry.field
    def tan(self) -> float:
        return math.tan(self.value)

    @strawberry.field
    def exp(self) -> float:
        return math.exp(min(self.value, 100))  # Prevent overflow

    @strawberry.field
    def factorial_mod(self) -> int:
        """Factorial of value mod 10."""
        n = abs(int(self.value)) % 10
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result

    @strawberry.field
    def is_prime_ish(self) -> bool:
        """Check if integer part is prime-ish."""
        n = abs(int(self.value))
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        return all(n % i != 0 for i in range(3, min(int(n**0.5) + 1, 100), 2))

    @strawberry.field
    def fibonacci_term(self) -> int:
        """Nth fibonacci number where n = value % 20."""
        n = abs(int(self.value)) % 20
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    @strawberry.field
    def harmonic_sum(self) -> float:
        """Sum of 1/1 + 1/2 + ... + 1/n."""
        n = max(1, abs(int(self.value)) % 100)
        return sum(1 / i for i in range(1, n + 1))

    @strawberry.field
    def geometric_mean(self) -> float:
        """Geometric mean with next 5 values."""
        values = [abs(self.value) + i for i in range(5)]
        product = 1
        for v in values:
            product *= v
        return product ** (1 / len(values))

    @strawberry.field
    def standard_deviation(self) -> float:
        """Standard deviation of value and variations."""
        values = [self.value + i * 0.1 for i in range(-5, 6)]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)


@strawberry.type
class DataPoint:
    id: int
    x: float
    y: float
    z: float

    @strawberry.field
    def magnitude(self) -> float:
        """3D vector magnitude."""
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    @strawberry.field
    def normalized_x(self) -> float:
        mag = self.magnitude()
        return self.x / mag if mag > 0 else 0

    @strawberry.field
    def normalized_y(self) -> float:
        mag = self.magnitude()
        return self.y / mag if mag > 0 else 0

    @strawberry.field
    def normalized_z(self) -> float:
        mag = self.magnitude()
        return self.z / mag if mag > 0 else 0

    @strawberry.field
    def dot_product_with_unit(self) -> float:
        """Dot product with unit vector (1,1,1)/sqrt(3)."""
        unit = 1 / math.sqrt(3)
        return self.x * unit + self.y * unit + self.z * unit

    @strawberry.field
    def angle_from_origin(self) -> float:
        """Angle in radians from origin."""
        return math.atan2(math.sqrt(self.x**2 + self.y**2), self.z)

    @strawberry.field
    def spherical_phi(self) -> float:
        """Spherical coordinate phi."""
        return math.atan2(self.y, self.x)

    @strawberry.field
    def spherical_theta(self) -> float:
        """Spherical coordinate theta."""
        mag = self.magnitude()
        return math.acos(self.z / mag) if mag > 0 else 0

    @strawberry.field
    def spherical_r(self) -> float:
        """Spherical coordinate r."""
        return self.magnitude()

    @strawberry.field
    def distance_from_plane(self) -> float:
        """Distance from plane x + y + z = 1."""
        numerator = abs(self.x + self.y + self.z - 1)
        denominator = math.sqrt(3)
        return numerator / denominator

    @strawberry.field
    def projection_on_xy(self) -> float:
        """Length of projection on XY plane."""
        return math.sqrt(self.x**2 + self.y**2)

    @strawberry.field
    def projection_on_xz(self) -> float:
        """Length of projection on XZ plane."""
        return math.sqrt(self.x**2 + self.z**2)

    @strawberry.field
    def projection_on_yz(self) -> float:
        """Length of projection on YZ plane."""
        return math.sqrt(self.y**2 + self.z**2)

    @strawberry.field
    def quadrant(self) -> int:
        """Which 3D quadrant (1-8)."""
        q = 1
        if self.x < 0:
            q += 4
        if self.y < 0:
            q += 2
        if self.z < 0:
            q += 1
        return q

    @strawberry.field
    def metrics_x(self) -> Metrics:
        """Metrics for X coordinate."""
        return Metrics(value=self.x)

    @strawberry.field
    def metrics_y(self) -> Metrics:
        """Metrics for Y coordinate."""
        return Metrics(value=self.y)

    @strawberry.field
    def metrics_z(self) -> Metrics:
        """Metrics for Z coordinate."""
        return Metrics(value=self.z)

    @strawberry.field
    def metrics_magnitude(self) -> Metrics:
        """Metrics for magnitude."""
        return Metrics(value=self.magnitude())


@strawberry.type
class Dataset:
    name: str
    size: int

    @strawberry.field
    def points(self) -> list[DataPoint]:
        """Generate data points."""
        points = []
        for i in range(self.size):
            # Use deterministic values
            angle = (i * 2 * math.pi) / self.size
            radius = 1 + (i % 10) * 0.1
            points.append(
                DataPoint(
                    id=i,
                    x=radius * math.cos(angle),
                    y=radius * math.sin(angle),
                    z=math.sin(i * 0.1) * 2,
                )
            )
        return points

    @strawberry.field
    def summary_mean_x(self) -> float:
        """Mean of all X coordinates."""
        points = self.points()
        return sum(p.x for p in points) / len(points) if points else 0

    @strawberry.field
    def summary_mean_y(self) -> float:
        """Mean of all Y coordinates."""
        points = self.points()
        return sum(p.y for p in points) / len(points) if points else 0

    @strawberry.field
    def summary_mean_z(self) -> float:
        """Mean of all Z coordinates."""
        points = self.points()
        return sum(p.z for p in points) / len(points) if points else 0

    @strawberry.field
    def summary_std_x(self) -> float:
        """Standard deviation of X coordinates."""
        points = self.points()
        if not points:
            return 0
        mean = self.summary_mean_x()
        variance = sum((p.x - mean) ** 2 for p in points) / len(points)
        return math.sqrt(variance)

    @strawberry.field
    def summary_std_y(self) -> float:
        """Standard deviation of Y coordinates."""
        points = self.points()
        if not points:
            return 0
        mean = self.summary_mean_y()
        variance = sum((p.y - mean) ** 2 for p in points) / len(points)
        return math.sqrt(variance)

    @strawberry.field
    def summary_std_z(self) -> float:
        """Standard deviation of Z coordinates."""
        points = self.points()
        if not points:
            return 0
        mean = self.summary_mean_z()
        variance = sum((p.z - mean) ** 2 for p in points) / len(points)
        return math.sqrt(variance)


@strawberry.type
class Query:
    @strawberry.field
    def datasets(self, count: int = 5, points_per_dataset: int = 100) -> list[Dataset]:
        """Generate multiple datasets."""
        return [
            Dataset(name=f"Dataset-{i}", size=points_per_dataset) for i in range(count)
        ]

    @strawberry.field
    def large_dataset(self) -> Dataset:
        """Single large dataset."""
        return Dataset(name="Large", size=500)


def run_pure_computation_benchmark() -> None:
    """Benchmark pure computation to show dramatic JIT benefits."""
    schema = strawberry.Schema(Query)

    # Query with massive pure computation
    query = """
    query PureComputation {
        datasets(count: 10, pointsPerDataset: 100) {
            name
            size
            summaryMeanX
            summaryMeanY
            summaryMeanZ
            summaryStdX
            summaryStdY
            summaryStdZ

            points {
                id
                x
                y
                z
                magnitude
                normalizedX
                normalizedY
                normalizedZ
                dotProductWithUnit
                angleFromOrigin
                sphericalPhi
                sphericalTheta
                sphericalR
                distanceFromPlane
                projectionOnXy
                projectionOnXz
                projectionOnYz
                quadrant

                metricsX {
                    value
                    squared
                    cubed
                    sqrt
                    log
                    sin
                    cos
                    tan
                    exp
                    factorialMod
                    isPrimeIsh
                    fibonacciTerm
                    harmonicSum
                    geometricMean
                    standardDeviation
                }

                metricsY {
                    squared
                    cubed
                    sqrt
                    log
                    sin
                    cos
                }

                metricsZ {
                    squared
                    cubed
                    sqrt
                    log
                }

                metricsMagnitude {
                    squared
                    cubed
                    sqrt
                }
            }
        }
    }
    """

    root = Query()

    # Warm up
    for _ in range(2):
        execute_sync(schema._schema, parse(query), root_value=root)

    # 1. Standard GraphQL
    iterations = 5
    times = []
    for i in range(iterations):
        start = time.perf_counter()
        execute_sync(schema._schema, parse(query), root_value=root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    standard_avg = statistics.mean(times) * 1000
    min(times) * 1000
    max(times) * 1000

    # Approximate computation count
    datasets = 10
    points_per_dataset = 100
    total_points = datasets * points_per_dataset
    fields_per_point = 18
    metrics_fields = 15 + 7 + 4 + 4  # x + y + z + magnitude
    total_computations = (
        total_points * (fields_per_point + metrics_fields) + datasets * 6
    )

    # 2. JIT Compiled
    start_compile = time.perf_counter()
    compiled_fn = compile_query(schema, query)
    (time.perf_counter() - start_compile) * 1000

    times = []
    for i in range(iterations):
        start = time.perf_counter()
        compiled_fn(root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    jit_avg = statistics.mean(times) * 1000
    min(times) * 1000
    max(times) * 1000

    # 3. Production simulation with cache
    compiler = CachedJITCompiler(schema)

    times = []
    for i in range(20):
        start = time.perf_counter()
        fn = compiler.compile_query(query)
        fn(root)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        if i == 0:
            pass

    statistics.mean(times) * 1000
    avg_cached = statistics.mean(times[1:]) * 1000  # Exclude first

    compiler.get_cache_stats()

    # Summary

    standard_avg / jit_avg
    standard_avg / avg_cached

    (1_000_000 / total_computations) * standard_avg / 1000
    (1_000_000 / total_computations) * jit_avg / 1000
    (1_000_000 / total_computations) * avg_cached / 1000


if __name__ == "__main__":
    run_pure_computation_benchmark()
