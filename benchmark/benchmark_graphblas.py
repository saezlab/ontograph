#!/usr/bin/env python3
"""Fairer benchmark for ClientOntology methods using the graphblas backend."""

from __future__ import annotations

import io
import time
from contextlib import redirect_stdout
import statistics

from ontograph.client import ClientOntology

BACKEND = 'graphblas'
SOURCE = 'chebi'
CACHE_DIR = './data/out'
WARMUP_RUNS = 1
MEASURE_RUNS = 5
EASY_TERM_ID = 'CHEBI:36341'
MEDIUM_TERM_ID = 'CHEBI:46662'
HARD_TERM_ID = 'CHEBI:26671'


def _term_id(term: object) -> str:
    return getattr(term, 'id', str(term))


def _ids(values: list | set) -> list[str]:
    return sorted({_term_id(v) for v in values})


def _normalize_distance_pairs(
    pairs: list[tuple[object, int]],
) -> list[tuple[str, int]]:
    normalized = []
    for node, distance in pairs:
        normalized.append((_term_id(node), abs(int(distance))))
    return normalized


def _count_terms(client: ClientOntology) -> int:
    graph = client._get_ontology
    return int(getattr(graph, 'number_nodes', 0))


def _result_size(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1
    if isinstance(value, (list, set, tuple, dict, str)):
        return len(value)
    return 1


def _benchmark_callable(
    name: str, func, warmup_runs: int, measure_runs: int
) -> dict:
    for _ in range(warmup_runs):
        func()

    samples_ms: list[float] = []
    last_value = None
    for _ in range(measure_runs):
        t0 = time.perf_counter()
        last_value = func()
        samples_ms.append((time.perf_counter() - t0) * 1000.0)

    median_ms = statistics.median(samples_ms)

    return {
        'name': name,
        'status': 'ok',
        'warmup_runs_count': warmup_runs,
        'measure_runs_count': measure_runs,
        'time_median_ms': median_ms,
        'result_size_count': _result_size(last_value),
    }


def _run_benchmark(
    name: str, func, warmup_runs: int, measure_runs: int
) -> dict:
    try:
        return _benchmark_callable(name, func, warmup_runs, measure_runs)
    except Exception as exc:
        return {
            'name': name,
            'status': f'error: {exc}',
            'warmup_runs_count': warmup_runs,
            'measure_runs_count': measure_runs,
            'time_median_ms': None,
            'result_size_count': None,
        }


def _choose_term_set(client: ClientOntology) -> dict:
    roots = client.get_root()
    root_id = _term_id(roots[0]) if roots else None

    easy_term_id = EASY_TERM_ID
    medium_term_id = MEDIUM_TERM_ID
    hard_term_id = HARD_TERM_ID

    try:
        easy_depth = client.get_distance_from_root(easy_term_id)
    except Exception:
        easy_depth = None
    try:
        medium_depth = client.get_distance_from_root(medium_term_id)
    except Exception:
        medium_depth = None
    try:
        hard_depth = client.get_distance_from_root(hard_term_id)
    except Exception:
        hard_depth = None

    ancestors_hard = _normalize_distance_pairs(
        list(client.get_ancestors_with_distance(hard_term_id))
    )
    ancestor_candidates = sorted(
        (term_id, depth) for term_id, depth in ancestors_hard if depth >= 2
    )
    if ancestor_candidates:
        ancestor_hard_id = ancestor_candidates[0][0]
    else:
        parent_candidates = _ids(client.get_parents(hard_term_id))
        ancestor_hard_id = (
            parent_candidates[0] if parent_candidates else root_id
        )

    siblings_medium = [
        s
        for s in _ids(client.get_siblings(medium_term_id))
        if s != medium_term_id
    ]
    if siblings_medium:
        sibling_medium_id = siblings_medium[0]
    else:
        parent_candidates = _ids(client.get_parents(medium_term_id))
        if parent_candidates:
            neighbor_candidates = [
                t
                for t in _ids(client.get_children(parent_candidates[0]))
                if t != medium_term_id
            ]
            sibling_medium_id = (
                neighbor_candidates[0]
                if neighbor_candidates
                else medium_term_id
            )
        else:
            sibling_medium_id = medium_term_id

    return {
        'root_id': root_id,
        'easy_term_id': easy_term_id,
        'medium_term_id': medium_term_id,
        'hard_term_id': hard_term_id,
        'ancestor_hard_id': ancestor_hard_id,
        'sibling_medium_id': sibling_medium_id,
        'depth_easy_hops': easy_depth,
        'depth_medium_hops': medium_depth,
        'depth_hard_hops': hard_depth,
    }


def main() -> None:
    results: list[dict] = []

    # Prime cache (unmeasured) to avoid download/parsing cold-start in load benchmark.
    primer = ClientOntology(cache_dir=CACHE_DIR)
    primer.load(source=SOURCE, backend=BACKEND)

    results.append(
        _run_benchmark(
            name='load',
            func=lambda: ClientOntology(cache_dir=CACHE_DIR).load(
                source=SOURCE, backend=BACKEND
            ),
            warmup_runs=WARMUP_RUNS,
            measure_runs=MEASURE_RUNS,
        )
    )

    client = ClientOntology(cache_dir=CACHE_DIR)
    client.load(source=SOURCE, backend=BACKEND)

    term_count = _count_terms(client)
    term_set = _choose_term_set(client)

    root_id = term_set['root_id']
    easy_term_id = term_set['easy_term_id']
    medium_term_id = term_set['medium_term_id']
    hard_term_id = term_set['hard_term_id']
    ancestor_hard_id = term_set['ancestor_hard_id']
    sibling_medium_id = term_set['sibling_medium_id']

    trajectories_hard = (
        client.get_trajectories_from_root(hard_term_id) if hard_term_id else []
    )

    benchmarks = [
        ('get_root', lambda: client.get_root()),
        ('get_term', lambda: client.get_term(easy_term_id)),
        ('get_parents', lambda: client.get_parents(medium_term_id)),
        ('get_children', lambda: client.get_children(medium_term_id)),
        ('get_ancestors', lambda: client.get_ancestors(hard_term_id)),
        (
            'get_ancestors_with_distance',
            lambda: list(client.get_ancestors_with_distance(hard_term_id)),
        ),
        ('get_descendants', lambda: client.get_descendants(medium_term_id)),
        (
            'get_descendants_with_distance',
            lambda: list(client.get_descendants_with_distance(medium_term_id)),
        ),
        ('get_siblings', lambda: client.get_siblings(medium_term_id)),
        (
            'is_ancestor',
            lambda: client.is_ancestor(ancestor_hard_id, hard_term_id),
        ),
        (
            'is_descendant',
            lambda: client.is_descendant(hard_term_id, ancestor_hard_id),
        ),
        (
            'is_sibling',
            lambda: client.is_sibling(medium_term_id, sibling_medium_id),
        ),
        (
            'get_common_ancestors',
            lambda: client.get_common_ancestors(
                [medium_term_id, sibling_medium_id]
            ),
        ),
        (
            'get_lowest_common_ancestors',
            lambda: client.get_lowest_common_ancestors(
                [medium_term_id, sibling_medium_id]
            ),
        ),
        (
            'get_distance_from_root',
            lambda: client.get_distance_from_root(hard_term_id),
        ),
        (
            'get_path_between',
            lambda: client.get_path_between(ancestor_hard_id, hard_term_id),
        ),
        (
            'get_trajectories_from_root',
            lambda: client.get_trajectories_from_root(hard_term_id),
        ),
    ]

    def _print_trajectories() -> None:
        with redirect_stdout(io.StringIO()):
            client.print_term_trajectories_tree(trajectories_hard)

    benchmarks.append(('print_term_trajectories_tree', _print_trajectories))

    for name, func in benchmarks:
        results.append(
            _run_benchmark(
                name=name,
                func=func,
                warmup_runs=WARMUP_RUNS,
                measure_runs=MEASURE_RUNS,
            )
        )

    print(f'backend: {BACKEND}')
    print(f'source: {SOURCE}')
    print(f'cache_dir: {CACHE_DIR}')
    print('cache_primed: true [bool]')
    print(f'warmup_runs: {WARMUP_RUNS} [count]')
    print(f'measure_runs: {MEASURE_RUNS} [count]')
    print(f'terms_total: {term_count} [count]')
    print(f'term_root: {root_id} [term_id]')
    print(f'term_easy: {easy_term_id} [term_id]')
    print(f'term_medium: {medium_term_id} [term_id]')
    print(f'term_hard: {hard_term_id} [term_id]')
    print(f'term_ancestor_hard: {ancestor_hard_id} [term_id]')
    print(f'term_sibling_medium: {sibling_medium_id} [term_id]')
    print(f'depth_easy: {term_set["depth_easy_hops"]} [hops]')
    print(f'depth_medium: {term_set["depth_medium_hops"]} [hops]')
    print(f'depth_hard: {term_set["depth_hard_hops"]} [hops]')

    print('\nresults:')
    print(
        'method | status | warmup_runs_count [count] | measure_runs_count [count] | '
        'time_median_ms [ms] | '
        'result_size_count [count]'
    )
    for row in results:
        print(
            f'{row["name"]} | {row["status"]} | {row["warmup_runs_count"]} | {row["measure_runs_count"]} | '
            f'{row["time_median_ms"] if row["time_median_ms"] is not None else "NA"} | '
            f'{row["result_size_count"] if row["result_size_count"] is not None else "NA"}'
        )


if __name__ == '__main__':
    main()
