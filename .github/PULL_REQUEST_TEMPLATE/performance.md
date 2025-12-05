# Performance Pull Request

> When to use: Optimizations requiring benchmarks and documented methodology.

## Summary
- Related to #<issue-number>
- Area optimized (loader, queries, graph operations)

## Methodology
- Benchmark setup (hardware, dataset, parameters)
- Metrics: time, memory, throughput
- Baseline vs new results

## Changes
- What was optimized and how
- Trade-offs and risks

## Tests
- [ ] Performance tests or benchmarks included
- [ ] Functional tests still pass (`pytest -q`)

## Checklist
- [ ] Documented methodology and reproducibility
- [ ] Changelog entry prepared (see `CHANGELOG.md`)
- [ ] Monitoring/observability plan (if applicable)
- [ ] Labels set (performance)
- [ ] I agree to the [Code of Conduct](../CODE_OF_CONDUCT.md)

## Additional notes
- Future work or guardrails
