#!/usr/bin/env python3
"""Benchmark memory required to load CHEBI with memray, per backend.

This script has two modes:
1) Driver mode (default): orchestrates memray runs, generates HTML reports,
   parses peak memory, and prints/saves a summary.
2) Worker mode (--worker): performs only `ClientOntology.load(...)`.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from ontograph.client import ClientOntology

BACKENDS = ('pronto', 'graphblas')
DEFAULT_ONTOLOGY_ID = 'chebi'
DEFAULT_CACHE_DIR = './data/out'
DEFAULT_REPETITIONS = 5
DEFAULT_RESULTS_DIR = './benchmark/results'


def _to_mb(value: float, unit: str) -> float:
    unit = unit.upper()
    factors = {
        'B': 1 / (1024.0 * 1024.0),
        'KB': 1 / 1024.0,
        'MB': 1.0,
        'GB': 1024.0,
        'TB': 1024.0 * 1024.0,
    }
    if unit not in factors:
        raise ValueError(f'Unsupported unit: {unit}')
    return value * factors[unit]


def _parse_peak_memory_mb(memray_stats_output: str) -> float | None:
    match = re.search(
        r'Peak memory usage:\s*([0-9]+(?:\.[0-9]+)?)\s*([KMGTP]?B)',
        memray_stats_output,
    )
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    return _to_mb(value, unit)


def _run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )


def _prime_cache(cache_dir: str, ontology_id: str) -> None:
    client = ClientOntology(cache_dir=cache_dir)
    client.load(source=ontology_id, backend='pronto')


def _resolve_local_source(cache_dir: str, ontology_id: str) -> Path:
    cache_path = Path(cache_dir)
    preferred = cache_path / f'{ontology_id.lower()}.obo'
    if preferred.exists():
        return preferred

    candidates = sorted(
        list(cache_path.glob(f'{ontology_id.lower()}*.obo'))
        + list(cache_path.glob(f'*{ontology_id.lower()}*.obo'))
    )
    if candidates:
        return candidates[0]

    raise FileNotFoundError(
        f'Could not find local OBO file for "{ontology_id}" in {cache_path}. '
        'Prime cache first or pass --source-file.'
    )


def _worker_load(
    backend: str, source: str, cache_dir: str, include_obsolete: bool
) -> None:
    client = ClientOntology(cache_dir=cache_dir)
    client.load(
        source=source, backend=backend, include_obsolete=include_obsolete
    )


def _ensure_memray_installed() -> None:
    if shutil.which('memray') is None:
        raise RuntimeError(
            'memray executable not found. Install it (e.g., `uv add --dev memray`).'
        )


def _backend_rows(rows: list[dict], backend: str) -> list[dict]:
    return [row for row in rows if row['backend'] == backend]


def _write_artifacts(rows: list[dict], outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    json_path = outdir / 'summary.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2)

    csv_path = outdir / 'summary.csv'
    fieldnames = [
        'backend',
        'run',
        'status',
        'peak_memory_mb',
        'trace_file',
        'flamegraph_html',
        'leaks_flamegraph_html',
        'error',
    ]
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    'backend': row['backend'],
                    'run': row['run'],
                    'status': row['status'],
                    'peak_memory_mb': row.get('peak_memory_mb'),
                    'trace_file': row.get('trace_file'),
                    'flamegraph_html': row.get('flamegraph_html'),
                    'leaks_flamegraph_html': row.get('leaks_flamegraph_html'),
                    'error': row.get('error'),
                }
            )


def _print_summary(
    rows: list[dict],
    ontology_id: str,
    source_file: Path,
    cache_dir: str,
    repetitions: int,
    outdir: Path,
) -> None:
    print(f'ontology_id: {ontology_id}')
    print(f'source_file: {source_file}')
    print(f'cache_dir: {cache_dir}')
    print(f'repetitions: {repetitions}')
    print(f'artifacts_dir: {outdir}')
    print()
    print('backend | successful_runs | peak_memory_mb_median | peak_memory_mb_samples')

    for backend in BACKENDS:
        backend_rows = _backend_rows(rows, backend)
        samples = [
            row['peak_memory_mb']
            for row in backend_rows
            if row['status'] == 'ok' and row.get('peak_memory_mb') is not None
        ]
        if samples:
            median_mb = statistics.median(samples)
            sample_str = '[' + ', '.join(f'{v:.3f}' for v in samples) + ']'
            print(
                f'{backend} | {len(samples)} | {median_mb:.3f} | {sample_str}'
            )
        else:
            print(f'{backend} | 0 | NA | NA')


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Memray benchmark for CHEBI load memory per backend.'
    )
    parser.add_argument(
        '--backend',
        choices=(*BACKENDS, 'both'),
        default='both',
        help='Backend to benchmark (default: both).',
    )
    parser.add_argument(
        '--ontology-id',
        default=DEFAULT_ONTOLOGY_ID,
        help='Ontology ID to prime and locate locally (default: chebi).',
    )
    parser.add_argument(
        '--source-file',
        default=None,
        help='Local ontology file path to use for all runs.',
    )
    parser.add_argument(
        '--cache-dir',
        default=DEFAULT_CACHE_DIR,
        help='Cache directory (default: ./data/out).',
    )
    parser.add_argument(
        '--repetitions',
        type=int,
        default=DEFAULT_REPETITIONS,
        help='Repetitions per backend (default: 5).',
    )
    parser.add_argument(
        '--include-obsolete',
        action='store_true',
        help='Pass include_obsolete=True to client.load(...).',
    )
    parser.add_argument(
        '--results-dir',
        default=DEFAULT_RESULTS_DIR,
        help='Base directory for outputs (default: ./benchmark/results).',
    )
    parser.add_argument(
        '--worker',
        action='store_true',
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if args.worker:
        _worker_load(
            backend=args.backend,
            source=args.source_file,
            cache_dir=args.cache_dir,
            include_obsolete=args.include_obsolete,
        )
        return

    _ensure_memray_installed()

    # Prime cache and resolve a local file to avoid network/download noise.
    if args.source_file:
        source_file = Path(args.source_file)
        if not source_file.exists():
            raise FileNotFoundError(f'--source-file not found: {source_file}')
    else:
        _prime_cache(cache_dir=args.cache_dir, ontology_id=args.ontology_id)
        source_file = _resolve_local_source(
            cache_dir=args.cache_dir, ontology_id=args.ontology_id
        )

    selected_backends = BACKENDS if args.backend == 'both' else (args.backend,)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    outdir = Path(args.results_dir) / f'memory_memray_{timestamp}'
    outdir.mkdir(parents=True, exist_ok=True)

    script_path = Path(__file__).resolve()
    rows: list[dict] = []

    for backend in selected_backends:
        for run in range(1, args.repetitions + 1):
            trace_file = outdir / f'{backend}_run{run}.bin'
            flamegraph_html = outdir / f'{backend}_run{run}_flamegraph.html'
            leaks_flamegraph_html = (
                outdir / f'{backend}_run{run}_flamegraph_leaks.html'
            )

            row = {
                'backend': backend,
                'run': run,
                'status': 'ok',
                'peak_memory_mb': None,
                'trace_file': str(trace_file),
                'flamegraph_html': str(flamegraph_html),
                'leaks_flamegraph_html': str(leaks_flamegraph_html),
                'error': None,
            }

            try:
                run_cmd = [
                    'memray',
                    'run',
                    '-o',
                    str(trace_file),
                    str(script_path),
                    '--worker',
                    '--backend',
                    backend,
                    '--source-file',
                    str(source_file),
                    '--cache-dir',
                    args.cache_dir,
                ]
                if args.include_obsolete:
                    run_cmd.append('--include-obsolete')
                _run_command(run_cmd)

                stats_cmd = ['memray', 'stats', str(trace_file)]
                stats_out = _run_command(stats_cmd).stdout
                row['peak_memory_mb'] = _parse_peak_memory_mb(stats_out)

                flame_cmd = [
                    'memray',
                    'flamegraph',
                    '-o',
                    str(flamegraph_html),
                    str(trace_file),
                ]
                _run_command(flame_cmd)

                leaks_flame_cmd = [
                    'memray',
                    'flamegraph',
                    '--leaks',
                    '-o',
                    str(leaks_flamegraph_html),
                    str(trace_file),
                ]
                _run_command(leaks_flame_cmd)

            except subprocess.CalledProcessError as exc:
                row['status'] = 'error'
                row['error'] = (
                    f'Command failed: {" ".join(exc.cmd)}\n'
                    f'stdout:\n{exc.stdout}\n'
                    f'stderr:\n{exc.stderr}'
                )
            except Exception as exc:  # noqa: BLE001
                row['status'] = 'error'
                row['error'] = str(exc)

            rows.append(row)

    _write_artifacts(rows=rows, outdir=outdir)
    _print_summary(
        rows=rows,
        ontology_id=args.ontology_id,
        source_file=source_file,
        cache_dir=args.cache_dir,
        repetitions=args.repetitions,
        outdir=outdir,
    )


if __name__ == '__main__':
    main()
