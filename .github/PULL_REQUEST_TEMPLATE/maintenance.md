# Maintenance / Chore Pull Request

> When to use: Tooling, CI, dependency bumps, formatting, or code health.

## Summary
- Related to #<issue-number>
- Scope: tooling/CI/dependencies/formatting

## Changes
- Tools or CI jobs updated
- Dependencies bumped (versions, rationale)
- Rollback plan

## Reliability & Performance
- Impact assessment
- [ ] Performance checked if relevant

## Checklist
- [ ] Code style and pre-commit
  
	```bash
	pre-commit run -a
	```
- [ ] CI passes
- [ ] No secrets/credentials introduced
- [ ] Labels set (chore/maintenance)
- [ ] Changelog entry prepared (see `CHANGELOG.md`) if user-visible behavior changes
- [ ] I agree to the [Code of Conduct](../../CODE_OF_CONDUCT.md)

## Additional notes
- Risks or follow-ups
