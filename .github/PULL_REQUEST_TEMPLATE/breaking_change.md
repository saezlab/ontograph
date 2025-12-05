# Breaking Change Pull Request

> When to use: Changes that break backwards compatibility; requires a migration guide and communication plan.

## Summary
- Closes #<issue-number>
- Scope and rationale for breaking change

## Deprecation & Migration
- Deprecation path and timeline
- Migration guide and examples
- Scripts or tools to assist migration

## API / Data impacts
- Public API changes
- Data/schema changes

## Versioning & Communication
- Version bump strategy
- Communication plan (release notes, docs)

## Tests
- [ ] Updated tests for new behavior
- [ ] Migration tests where possible
- [ ] All tests pass locally (`pytest -q`)

## Documentation
- [ ] Docs updated (MkDocs) and README
- [ ] Clear migration instructions visible to users

## Checklist
- [ ] Backwards compatibility noted as broken (explicit)
- [ ] Changelog entry prepared (see `CHANGELOG.md`)
- [ ] Risk assessment and rollback plan
- [ ] Labels set (breaking-change)
- [ ] I agree to the [Code of Conduct](../CODE_OF_CONDUCT.md)

## Additional notes
- Known limitations and follow-ups
