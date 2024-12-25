from __future__ import annotations

import contextlib
import os
from importlib.metadata import version
from multiprocessing import Pool, cpu_count
from typing import TYPE_CHECKING, Any, Union

from libcst.codemod._cli import ExecutionConfig, ExecutionResult, _execute_transform
from libcst.codemod._dummy_pool import DummyPool
from rich.progress import Progress

from ._fake_progress import FakeProgress

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from libcst.codemod import Codemod

ProgressType = Union[type[Progress], type[FakeProgress]]
PoolType = Union[type[Pool], type[DummyPool]]  # type: ignore


def _get_libcst_version() -> tuple[int, int, int]:
    package_version_str = version("libcst")

    try:
        major, minor, patch = map(int, package_version_str.split("."))
    except ValueError:
        major, minor, patch = (0, 0, 0)

    return major, minor, patch


def _execute_transform_wrap(
    job: dict[str, Any],
) -> ExecutionResult:
    additional_kwargs: dict[str, Any] = {}

    if _get_libcst_version() >= (1, 4, 0):
        additional_kwargs["scratch"] = {}

    # TODO: maybe capture warnings?
    with open(os.devnull, "w") as null, contextlib.redirect_stderr(null):  # noqa: PTH123
        return _execute_transform(**job, **additional_kwargs)


def _get_progress_and_pool(
    total_files: int, jobs: int
) -> tuple[PoolType, ProgressType]:
    poll_impl: PoolType = Pool  # type: ignore
    progress_impl: ProgressType = Progress

    if total_files == 1 or jobs == 1:
        poll_impl = DummyPool

    if total_files == 1:
        progress_impl = FakeProgress

    return poll_impl, progress_impl


def run_codemod(
    codemod: Codemod,
    files: Sequence[str],
) -> Generator[ExecutionResult, None, None]:
    chunk_size = 4
    total = len(files)
    jobs = min(cpu_count(), (total + chunk_size - 1) // chunk_size)

    config = ExecutionConfig()

    pool_impl, progress_impl = _get_progress_and_pool(total, jobs)

    tasks = [
        {
            "transformer": codemod,
            "filename": filename,
            "config": config,
        }
        for filename in files
    ]

    with pool_impl(processes=jobs) as p, progress_impl() as progress:  # type: ignore
        task_id = progress.add_task("[cyan]Updating...", total=len(tasks))

        for result in p.imap_unordered(
            _execute_transform_wrap, tasks, chunksize=chunk_size
        ):
            progress.advance(task_id)

            yield result
