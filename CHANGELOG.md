# Changelog

## Unreleased

### v4.1.0-rc2 source candidate

- Fixed repository-level `AGENTS.md` policy so actual project delegation follows the installed Global selector instead of repository-local `.var/daily-profile.json`.
- Clarified that repository-local `.var/` is non-authoritative development state and cannot allow, block, or select an actual project Luna role.
- Aligned current documentation with the published RC1 real global upgrade and fresh-session G1-G7 evidence while keeping RC2 repository-context delegation validation pending.
- Changed no selector algorithm, state schema, ModelDial source, Global agent configuration, installer payload, or legacy migration behavior.

### v4.1.0-rc1 source candidate

- Added the official ModelDial API v1 as the Daily Selector primary source.
- Retained the official full snapshot JSON as the only network fallback, followed by the existing LKG and fail-closed behavior.
- Removed the Radar HTML runtime parser and fallback.
- Preserved the five-effort selection engine, Daily Profile and LKG schemas, installer manifest schema, and legacy `3.2` migration semantics.
- Added offline API schema, source-order, state-compatibility, and v4.0.0-to-RC1 installer lifecycle coverage.
- Kept real global upgrade, fresh-session runtime acceptance, tag, and release outside this source-candidate change.

### Documentation

- Added a Codex-executable setup contract around the existing transactional installer.
- Added bilingual navigation, immutable installation quick starts, and product-oriented daily-use guidance.
- Added validation, Release, and License badges plus documentation regression checks.

## v4.0.0

- Promoted the v4 native architecture to stable.
- Validated global custom Luna discovery.
- Validated daily native Luna routing.
- Validated automatic `AGENTS.md` delegation.
- Validated native leaf behavior.
- Validated native parallel execution.
- Validated the Sol final Acceptance Gate.
- Validated the clean installer lifecycle.
- Validated legacy 3.2 migration and rollback.
- Validated the real global migration.
- Removed mandatory Hook-based routing from the current architecture.

## v4.0.0-rc1

- Native Runtime Tests 1–5 passed.
- Validated native custom Luna routing through project custom agents.
- Validated automatic delegation through the `AGENTS.md` policy and Daily Profile selected role.
- Validated native leaf enforcement with `[agents] enabled = false`.
- Validated native parallel delegation with Sol-authored acceptance.
- Removed mandatory Hook architecture from the current runtime design.
- Formalized the stable five-role Luna layout for `low`, `medium`, `high`, `xhigh`, and `max`.
- Added explicit-target installer lifecycle validation for clean install, safe merges, idempotency, upgrade, manifest-owned legacy migration, backup, exact rollback, and uninstall.
- Hardened global migration for the exact legacy `3.2` schema, a dedicated global-safe AGENTS payload, explicit v4 state and selector CLI contracts, concurrent first-use locking, and no legacy-state conversion.
- Made the v4 manifest the atomic last-write commit marker; pre-commit failpoints roll back exactly, while post-commit legacy-manifest cleanup is independently retryable.
- Kept real global installation approval separate. Sandbox validation does not authorize writes to a user's Codex home, and clean global validation remains required before stable `v4.0.0`.

## v4.0.0-prototype (historical)

- Removed mandatory Hook routing from the core architecture.
- Added native project-scoped custom Luna agents with stable role names.
- Added the project-level `AGENTS.md` delegation and Sol acceptance policy.
- Retained the Daily ModelDial selector as a clean fixtures-first standard-library module.
- Added explicit first-party live-source validation, LKG, fail-closed behavior, and repo-local state.
- Added a separate native leaf experiment without changing the five formal agents.
- Added a dry-run installer plan, local capability probe, cross-platform CI, tests, and public-repository documentation.
