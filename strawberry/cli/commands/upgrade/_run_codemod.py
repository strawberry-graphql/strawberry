from __future__ import annotations

import contextlib
import os
from multiprocessing import Pool, cpu_count
from typing import TYPE_CHECKING, Any, Dict, Generator, Sequence, Type, Union

from libcst.codemod._cli import ExecutionConfig, ExecutionResult, _execute_transform
from libcst.codemod._dummy_pool import DummyPool
from rich.progress import Progress

from ._fake_progress import FakeProgress

if TYPE_CHECKING:
    from libcst.codemod import Codemod

ProgressType = Union[Type[Progress], Type[FakeProgress]]
PoolType = Union[Type[Pool], Type[DummyPool]]  # type: ignore


def _execute_transform_wrap(
    job: Dict[str, Any],
) -> ExecutionResult:
    # TODO: maybe capture warnings?
    with open(os.devnull, "w") as null:  # noqa: PTH123
        with contextlib.redirect_stderr(null):
            return _execute_transform(**job)


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
