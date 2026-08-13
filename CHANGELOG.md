# Changelog

## v4.1.0-rc4 (published prerelease)

- Fixed Delegation Receipt reason evidence-gating: `Luna unavailable` now requires current-task parent-visible availability failure evidence that arose naturally on the normal delegation path.
- Defined selector fail-closed/no-valid-role and native role, discovery, capability, or spawn/agent availability failures as valid observed evidence; no selector invocation, no child attempt, Sol retention, docs-only work, sequential dependencies, or no independent bounded work are not evidence of unavailability.
- Made `Luna unavailable` explicitly unavailable as a default Sol-only fallback. Ambiguous Sol-only cases use the most direct non-availability reason with parent-visible support.
- Preserved decision neutrality: Receipt generation cannot invoke a selector, capability probe, tool, child, or network, or write state, telemetry, or repository content to manufacture evidence.
- Bumped the installer payload version to `v4.1.0-rc4` with manifest schema `1`; added RC3→RC4 fake-home upgrade, backup, idempotency, exact rollback, ownership-conflict, policy, regression-matrix, and documentation coverage.
- Changed no selector, ModelDial logic, Luna role, effort, concurrency, native leaf behavior, config, state schema, delegation threshold, Task Contract, Context Firewall, Sol Acceptance, installer algorithm, or migration behavior.
- Passed the full repository suite `114/114` at source validation commit `95cfd53200a3fc53b50a48fe7ab251dcc6d5e00b`; Windows, Ubuntu, and macOS CI passed there and at final source pin `d17bea49fdb0710bb2101f1577045bed2477ff79`.
- Recorded the separately authorized real RC3→RC4 Global upgrade as `PASS`: result `UPGRADED`, two effective changes limited to the managed Global `AGENTS.md` block and manifest, second apply `IDEMPOTENT_PASS`, and rollback ready. Selector, five Luna agents, config, Daily Profile, and LKG remained unchanged.
- Recorded Runtime Cases A/B/C/D as `PASS`: Sol reasoning, three-child `luna_max` delegated parallel execution with zero grandchildren, no-independent-work regression, and controlled genuine-unavailability evidence gating with its negative control.
- Published `v4.1.0-rc4` as the current preview prerelease; `v4.0.0` remains stable. Recorded runtime evidence is environment-bounded and three-platform CI does not imply three-platform real Codex runtime validation.

## v4.1.0-rc3 (published prerelease)

- Added a low-noise final-line Delegation Receipt to the installer-managed Global `AGENTS.md` policy for receipt-eligible non-trivial work.
- Defined five conceptual outcomes: `DELEGATED`, `TASK_TOO_SMALL`, `SOL_REASONING_TASK`, `NO_INDEPENDENT_WORK`, and `LUNA_UNAVAILABLE`.
- Required delegated receipts to use the actual selected native role and actual direct-child count, with `parallel` only for parent-visible execution overlap.
- Kept the Receipt downstream of delegation decisions: it cannot lower the threshold, force spawn or parallelism, trigger extra selector, child, file, tool, or network work, add state or telemetry, expose private reasoning, or attest runtime behavior by itself.
- Bumped the installer payload version to `v4.1.0-rc3` because the owned Global policy block changes; added RC1-to-RC3 upgrade, ownership-conflict, rollback, policy, installer, and documentation coverage.
- Added bilingual Receipt interpretation plus Basic read-only and optional parallel self-tests.
- Recorded the separately authorized real RC1→RC3 Global upgrade as `PASS`: result `UPGRADED`, two effective changes limited to the managed Global `AGENTS.md` block and manifest, second apply `IDEMPOTENT_PASS`, and rollback ready. Selector, Luna agents, config, selector state and schema, Daily Profile, and LKG remained unchanged.
- Recorded fresh-session Sol-only Receipt `PASS` with zero direct children and delegated Receipt `PASS` with three direct `luna_max` children, `gpt-5.6-luna` at `max`, verified parallel overlap, zero grandchildren, native leaf behavior, and Sol acceptance.
- Passed the full repository suite `109/109` and Windows, Ubuntu, and macOS CI for the release source.

## v4.1.0-rc2

- Fixed repository-level `AGENTS.md` policy so actual project delegation follows the installed Global selector instead of repository-local `.var/daily-profile.json`.
- Clarified that repository-local `.var/` is non-authoritative development state and cannot allow, block, or select an actual project Luna role.
- Aligned current documentation with the published RC1 real global upgrade and fresh-session G1-G7 evidence.
- Recorded `FRESH_REPO_CONTEXT_DELEGATION_PASS` for the exact RC2 release source.
- Changed no selector algorithm, state schema, ModelDial source, Global agent configuration, installer payload, or legacy migration behavior.

## v4.1.0-rc1

- Added the official ModelDial API v1 as the Daily Selector primary source.
- Retained the official full snapshot JSON as the only network fallback, followed by the existing LKG and fail-closed behavior.
- Removed the Radar HTML runtime parser and fallback.
- Preserved the five-effort selection engine, Daily Profile and LKG schemas, installer manifest schema, and legacy `3.2` migration semantics.
- Added offline API schema, source-order, state-compatibility, and v4.0.0-to-RC1 installer lifecycle coverage.
- The subsequently published prerelease passed its separately authorized real global upgrade and fresh-session Global Runtime G1-G7 acceptance.

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
