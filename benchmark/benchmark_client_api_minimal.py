#!/usr/bin/env python3
"""Minimal benchmark for ClientOntology public API on the chebi ontology.

This script measures the execution time of each public ClientOntology method
using fixed term IDs and prints a compact results table.
"""

from __future__ import annotations

import io
import time
import argparse
from contextlib import redirect_stdout
import statistics

from ontograph.client import ClientOntology

SOURCE = 'chebi'
CACHE_DIR = './data/out'
TERM_A = 'CHEBI:50269'
TERM_B = 'CHEBI:85234'
WARMUP_RUNS = 1
MEASURE_RUNS = 5
BACKENDS = ('pronto', 'graphblas')


def _result_size(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1
    if isinstance(value, (list, set, tuple, dict, str)):
        return len(value)
    return 1


def _benchmark_callable(
    func, warmup_runs: int, measure_runs: int
) -> tuple[float, object]:
    for _ in range(warmup_runs):
        func()

    samples_ms: list[float] = []
    last_value = None
    for _ in range(measure_runs):
        t0 = time.perf_counter()
        last_value = func()
        samples_ms.append((time.perf_counter() - t0) * 1000.0)

    return statistics.median(samples_ms), last_value


def _run_benchmark(
    name: str,
    func,
    warmup_runs: int,
    measure_runs: int,
) -> dict:
    try:
        time_median_ms, last_value = _benchmark_callable(
            func=func,
            warmup_runs=warmup_runs,
            measure_runs=measure_runs,
        )
        return {
            'name': name,
            'status': 'ok',
            'time_median_ms': time_median_ms,
            'result_size_count': _result_size(last_value),
        }
    except Exception as exc:
        return {
            'name': name,
            'status': f'error: {exc}',
            'time_median_ms': None,
            'result_size_count': None,
        }


def _build_benchmarks(client: ClientOntology) -> list[tuple[str, object]]:
    prepared_trajectories = []
    try:
        prepared_trajectories = client.get_trajectories_from_root(TERM_A)
    except Exception:
        prepared_trajectories = []

    def _print_trajectories() -> None:
        with redirect_stdout(io.StringIO()):
            client.print_term_trajectories_tree(prepared_trajectories)

    return [
        ('get_term', lambda: client.get_term(TERM_A)),
        ('get_parents', lambda: client.get_parents(TERM_A)),
        ('get_children', lambda: client.get_children(TERM_A)),
        ('get_ancestors', lambda: client.get_ancestors(TERM_A)),
        (
            'get_ancestors_with_distance',
            lambda: list(client.get_ancestors_with_distance(TERM_A)),
        ),
        ('get_descendants', lambda: client.get_descendants(TERM_A)),
        (
            'get_descendants_with_distance',
            lambda: list(client.get_descendants_with_distance(TERM_A)),
        ),
        ('get_siblings', lambda: client.get_siblings(TERM_A)),
        ('get_root', lambda: client.get_root()),
        ('is_ancestor', lambda: client.is_ancestor(TERM_A, TERM_B)),
        ('is_descendant', lambda: client.is_descendant(TERM_A, TERM_B)),
        ('is_sibling', lambda: client.is_sibling(TERM_A, TERM_B)),
        (
            'get_common_ancestors',
            lambda: client.get_common_ancestors([TERM_A, TERM_B]),
        ),
        (
            'get_lowest_common_ancestors',
            lambda: client.get_lowest_common_ancestors([TERM_A, TERM_B]),
        ),
        (
            'get_distance_from_root',
            lambda: client.get_distance_from_root(TERM_A),
        ),
        ('get_path_between', lambda: client.get_path_between(TERM_A, TERM_B)),
        (
            'get_trajectories_from_root',
            lambda: client.get_trajectories_from_root(TERM_A),
        ),
        ('print_term_trajectories_tree', _print_trajectories),
    ]


def _run_backend(backend: str) -> list[dict]:
    results: list[dict] = []

    # Cache warm-up out of measurement.
    primer = ClientOntology(cache_dir=CACHE_DIR)
    primer.load(source=SOURCE, backend=backend)

    results.append(
        _run_benchmark(
            name='load',
            func=lambda: ClientOntology(cache_dir=CACHE_DIR).load(
                source=SOURCE, backend=backend
            ),
            warmup_runs=WARMUP_RUNS,
            measure_runs=MEASURE_RUNS,
        )
    )

    client = ClientOntology(cache_dir=CACHE_DIR)
    client.load(source=SOURCE, backend=backend)

    for name, func in _build_benchmarks(client):
        results.append(
            _run_benchmark(
                name=name,
                func=func,
                warmup_runs=WARMUP_RUNS,
                measure_runs=MEASURE_RUNS,
            )
        )

    return results


def _print_results(backend: str, results: list[dict]) -> None:
    print(f'backend: {backend}')
    print(f'source: {SOURCE}')
    print(f'cache_dir: {CACHE_DIR}')
    print(f'term_a: {TERM_A}')
    print(f'term_b: {TERM_B}')
    print(f'warmup_runs: {WARMUP_RUNS}')
    print(f'measure_runs: {MEASURE_RUNS}')
    print()
    print('method | status | time_median_ms | result_size_count')
    for row in results:
        time_value = (
            f'{row["time_median_ms"]:.6f}'
            if row['time_median_ms'] is not None
            else 'NA'
        )
        result_size = (
            str(row['result_size_count'])
            if row['result_size_count'] is not None
            else 'NA'
        )
        print(f'{row["name"]} | {row["status"]} | {time_value} | {result_size}')
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Minimal ClientOntology benchmark for chebi terms.'
    )
    parser.add_argument(
        '--backend',
        choices=(*BACKENDS, 'both'),
        default='both',
        help='Backend to benchmark (default: both).',
    )
    args = parser.parse_args()

    selected_backends = BACKENDS if args.backend == 'both' else (args.backend,)
    for backend in selected_backends:
        results = _run_backend(backend)
        _print_results(backend=backend, results=results)


if __name__ == '__main__':
    main()
