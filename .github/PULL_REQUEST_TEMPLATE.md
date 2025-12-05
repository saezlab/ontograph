# Pull Request

> When to use: Use this default template for most changes (features, small fixes, refactors, docs). If your change is a bug fix, performance optimization, maintenance/chore, or a breaking change, consider using one of the specialized templates under `.github/PULL_REQUEST_TEMPLATE/`.

Thank you for contributing to OntoGraph! Please fill out the sections below to help us review efficiently.

## Summary

- Link to issue(s): Closes #<issue-number> (or) Related to #<issue-number>
- Brief description of the change:

## Type of change

Select one or more:
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] Feature (non-breaking change that adds functionality)
- [ ] Documentation update
- [ ] Refactor/maintenance (no functional change)
- [ ] Performance improvement
- [ ] CI/CD or tooling
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)

## Changes

- High-level list of changes (modules, major functions/classes touched)
- Any data files or schema changes
- Any API changes (inputs/outputs, public interfaces)

## Screenshots or demos (optional)

If relevant, include images, terminal outputs, or notebook snippets.

## Checklist

- Code quality & style
  - [ ] Follows project style and conventions
  - [ ] Pre-commit hooks run locally
    
    ```bash
    pre-commit run -a
    ```
- Tests
  - [ ] Unit tests added/updated
  - [ ] All tests pass locally (`pytest`) 
  - [ ] Includes edge cases (empty/null, invalid input, large inputs)
- Documentation
  - [ ] User docs updated (MkDocs in `docs/` as needed)
  - [ ] README updated if behavior or usage changed
  - [ ] Docstrings and comments added where helpful
- Reliability
  - [ ] No secrets or credentials in code or history
  - [ ] Backwards compatibility considered; migration notes added if breaking
  - [ ] Performance implications considered (time/memory), benchmarks if relevant
- Project hygiene
  - [ ] Linked issues referenced with `Closes #...` or `Related to #...`
  - [ ] Changelog entry prepared (see `CHANGELOG.md`)
  - [ ] Labels applied (bug, enhancement, docs, etc.)
- Community standards
  - [ ] I have read and agree to the [Code of Conduct](../CODE_OF_CONDUCT.md)

## Test plan

Describe how you tested the changes. Include commands, datasets, and expected outcomes. If applicable, reference tests in `tests/`:

```bash
# Example (adjust as needed)
pytest -q
```

## Breaking changes (if any)

- Describe what breaks and how users should migrate.
- Provide a migration example or script if possible.

## Additional context

- Risks, trade-offs, or follow-up tasks
- Dependencies or environment changes
- Related PRs
