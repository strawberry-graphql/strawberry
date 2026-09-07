# Strawberry benchmarks

This directory is the authoritative suite for current Strawberry. Benchmarks verify
GraphQL errors, output shapes and workload sizes as well as measuring execution.
CPU simulation, native wall-clock time and allocations are different measurements;
never splice their results into one time series.

## Run locally

Install the locked environment, then run the correctness checks without timing:

```sh
uv sync --locked
uv run pytest tests/benchmarks tests/test_benchmark_contracts.py -p no:codeflash-benchmark
```

`pytest-codspeed` owns the benchmark fixture. Disable the Codeflash benchmark
plugin explicitly so that plugin discovery cannot silently select another fixture.
Without `--codspeed`, each callback executes once and its assertions still run.

For native elapsed-time measurements, run serially on an otherwise idle machine:

```sh
uv run python -m tests.benchmarks.metadata benchmark-artifacts/environment.json --instrument walltime
uv run pytest tests/benchmarks --codspeed --codspeed-mode walltime \
  -p no:codeflash-benchmark -m 'not benchmark_stress' \
  --codspeed-warmup-time 0.1 --codspeed-max-time 1 --codspeed-max-rounds 30 \
  --junitxml=benchmark-artifacts/results.xml -o junit_family=legacy
```

Raw measurements are written to `.codspeed/results_*.json`. Archive these with
`benchmark-artifacts/`; HTTP response byte counts are in the JUnit properties.
Local timings are observations, not directly comparable with another machine.

CPU simulation and allocation measurements run through the CodSpeed action in CI.
A local instrumented simulation/memory run additionally requires the appropriate
CodSpeed runner; passing `--codspeed-mode simulation` alone does not install it.
See [CodSpeed's Python documentation](https://codspeed.io/docs/benchmarks/python).

## Workload groups

| Marker | Execution | Purpose |
| --- | --- | --- |
| Neither native nor stress | Every PR/main push, Python 3.14.7, four CodSpeed simulation shards | CPU regression detection |
| `benchmark_native` | Scheduled native runs | ASGI/FastAPI request parsing through response consumption, and fresh-process import/schema startup |
| `benchmark_stress` | Weekly or explicitly requested native runs | Largest argument lists, interface counts, stadium datasets and subscription streams |
| `benchmark_memory` | Scheduled Linux CodSpeed memory job | Schema construction, large result construction, cache churn and subscription cleanup |

Markers may overlap. A plain correctness run covers every group. The native
workflow in `strawberry-graphql/benchmarks` uses the existing Mac runner with Python
3.12.13 and 3.14.7, serially; do not compare the Python versions as the same series.
The main repository's `benchmark-memory.yml` runs bounded allocation workloads.
New native and memory results are advisory; the workflows do not invent regression
thresholds or change the repository's existing CodSpeed gate settings.

## Measurement boundaries

- Schemas, queries, expected responses and reusable fixtures are prepared outside
  the timed callback unless construction is explicitly the workload.
- Async execution uses `benchmark_loop`, with loop creation and shutdown outside
  timing. Driving the loop, coroutine creation and resolver work stay measured.
- The matched async resolver yields once with `sleep(0)`; it models scheduling,
  not database or network latency. DataLoader uses the same convention.
- Cache benchmarks reset shared module-level caches before **each round** with
  `benchmark.pedantic(..., iterations=1)`. Warm cases prime outside measurement;
  assertions verify the hit/miss contract. New schemas alone do not reset caches.
- Result assertions run after measurement. Subscription cases collect returned
  results, verify the exact count and payloads, and explicitly close generators.
  The setup case measures 100 setup/first-event/close cycles; the stream case
  includes consuming and retaining its requested event count.
- Federation entity inputs are recreated outside timing before every round,
  because entity resolution consumes the representation's `__typename` key.
- The stadium and application workloads intentionally construct resolver data.
  The matched execution workload reuses prepared objects to isolate execution.
- Schema construction starts from already-decorated types. The process-startup
  case intentionally includes interpreter launch, import, decoration, schema
  construction and a small verified query.
- HTTP uses an in-process HTTPX ASGI transport. It includes client/transport work,
  request parsing, execution, JSON encoding and response consumption, but no
  socket, network or external database. Fixed requests use compact JSON responses;
  both decoded content and exact response bytes are checked.
- CodSpeed disables cyclic GC during measurements. Allocator/RSS measurements
  and repeated subscription cleanup are diagnostic; a single sample is not proof
  of a leak. Collect sustained native runs when investigating retention.

## Comparing revisions

Metadata records the code revision, worktree-change flag, workload digest, lockfile
digest, Python build, platform, resolved packages, GC/cache policies and runner
identity. Keep those artifacts with results. Do not compare uncommitted working trees as
published baselines. Capture actual hardware identity and runner changes when
moving the native job; an architecture label alone does not identify a CPU.

To attribute a change to Strawberry, run the **same benchmark code and dependencies**
against both source revisions. A changed lockfile is a dependency experiment as
well as a code change. If an old version cannot execute the new workload, record
it as unsupported rather than turning its error into a timing. Run unchanged
revisions repeatedly to establish variability before adding per-case thresholds.
CPU estimates are not measured HTTP latency; round timings are not request p95/p99.
Missing, skipped or failed runs are not performance improvements.

## Suite version 2 and historical continuity

Functions renamed with `_v2` intentionally start new series:

- Argument conversion excludes configuration construction and the full-list assertion.
- Application, interface, complex/generic, extension, stadium and DataLoader
  execution exclude loop setup/shutdown. Application data uses a fixed date and
  deterministic pets; complex schema IDs now use their seed instead of `str(int)`.
- Extension benchmarks use classes/factories rather than deprecated shared instances.
- Subscription measurements close streams and collect results for complete validation.
- Parser-cache cases have explicit uncached/cold/warm contracts, and optionally
  include the validation cache.

Existing synchronous execution and exception-handler timings keep their names
because their new assertions run outside the measured callback. The awaitable
benchmarks added separately in main retain their existing definitions and IDs.
Stress sizes retain their parameter IDs, even though their measurement schedule
changes. The stadium adds a smaller 1,800-seat PR case; the 45,000/90,000-seat cases
are available as stress cases.

The public ASV archive at [speed.strawberry.rocks](https://speed.strawberry.rocks/)
is preserved separately. Its legacy directive fixture can return validation errors
on current Strawberry, and old measurements lack current correctness guarantees.
Do not infer a runtime improvement from that series without reproducing the
historical workload successfully.
