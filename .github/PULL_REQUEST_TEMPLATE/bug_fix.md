# Bug Fix Pull Request

> When to use: Fixing a reported issue or regression. Emphasizes reproduction, root cause, and regression tests.

## Summary
- Closes #<issue-number>
- Brief description of the bug and fix

## Environment and reproduction
- Affected version(s):
- OS / Python / dependencies:
- Reproduction steps:
  1. ...
  2. ...
  3. Expected vs actual behavior:

## Root cause analysis
- What caused the bug?
- Why wasn’t it caught earlier?
- Areas impacted:

## Fix details
- Approach and scope
- Any trade-offs
- Risk assessment

## Tests
- [ ] Regression test added/updated
- [ ] Edge cases covered (empty/null, invalid input, large inputs)
- [ ] All tests pass locally (`pytest -q`)

## Documentation
- [ ] User docs updated if behavior changed (`docs/`)
- [ ] README updated if usage changed

## Checklist
- [ ] Code style and pre-commit
  
  ```bash
  pre-commit run -a
  ```
- [ ] Performance impact considered
- [ ] No secrets/credentials introduced
- [ ] Labels set (bug)
- [ ] Changelog entry prepared (see `CHANGELOG.md`)
- [ ] I agree to the [Code of Conduct](../CODE_OF_CONDUCT.md)

## Test plan
Describe how you validated the fix.

## Additional notes
- Follow-ups or monitoring plan
