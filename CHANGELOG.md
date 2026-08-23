# Changelog

## v4.1.0 (published Stable release)

- Added Stable Source Commit A `67a72f8accc5d53ef04ff8d64d8838e397ceecda`; local repository validation and exact-SHA CI passed on Windows, Ubuntu, and macOS.
- Promoted the installer payload from `v4.1.0-rc6` to `v4.1.0` while retaining manifest schema `1` and the RC6 selector, policy, agent, and config payloads byte-for-byte.
- Added RC6→Stable fake-home lifecycle coverage. The upgrade changes only `sol-luna-v4/install-manifest.json` and verifies dry-run zero writes, transaction backup, second-apply idempotency, exact rollback, downgrade refusal, and ownership conflict fail-closed behavior.
- Recorded an independent pre-publication fresh-task compatibility smoke `PASS` for CLI, Luna capability, Selector, Delegation, Protected state, Runtime contract, and final Compatibility against the unchanged installed product runtime. No real Global Stable apply was performed.
- Retained the RC6 real Global upgrade, O1–O10 runtime acceptance, Final O4/O9 re-certification, and Runtime Cases A/B/C/D as bounded historical evidence from one native Windows Codex environment. This does not imply three-platform real-runtime validation or universal compatibility.
- Prepared the reviewed Stable setup contract around the immutable Stable Source Commit A. The public installation entry pins that contract through a separate exact immutable documentation commit, not a mutable branch or the runtime source itself.
- Preserved the annotated `v4.1.0-rc6` tag and its GitHub Prerelease unchanged as historical Public Beta evidence. RC5 remains an older historical Preview.

## v4.1.0-rc6 (published historical prerelease)

- Added the RC6 runtime source at Source Commit A `50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49`; exact-SHA CI passed on Windows, Ubuntu, and macOS.
- Published annotated tag `v4.1.0-rc6`, peeled to release-preparation Commit `969e2b311df54c43168c4e1bfe5a28661041d50b`, as a GitHub Prerelease / Preview / Public Beta. RC6 later became historical and `v4.1.0-rc5` is an older historical Preview.
- The reviewed RC6 setup contract is `CODEX_SOL_LUNA_SETUP.md`. Public installation entries pin it by an exact immutable documentation commit that is distinct from runtime Source Commit A.
- Bumped the source installer payload to `v4.1.0-rc6` while retaining manifest schema `1`. RC5→RC6 fake-home lifecycle coverage expects only `sol-luna-v4/selector.py` and `sol-luna-v4/install-manifest.json` to change, with idempotency, backup, exact rollback, and ownership fail-closed checks.
- Normalized malformed URL parsing, hostname, and port `ValueError` cases inside the selector to `SnapshotInvalid`, preserving the API → snapshot → LKG → fail-closed source order.
- Added the compatibility-smoke baseline with dual exact rollout roots and bounded writer-settle/fail-closed evidence. The harness does not modify product runtime.
- Recorded the separately authorized real RC5→RC6 Global upgrade as `PASS` in one native Windows Codex environment: result `UPGRADED`, effective changes limited to `sol-luna-v4/selector.py` and `sol-luna-v4/install-manifest.json`, second apply `IDEMPOTENT_PASS`, and the installer-owned rollback snapshot verified by hash. Global policy, config, five Luna agents, Daily Profile, and LKG remained unchanged.
- Recorded fresh-task compatibility smoke, O1-O10 runtime acceptance, Final O4/O9 re-certification, and Runtime Cases A/B/C/D as `PASS`. Parent-visible rollout metadata, not Receipt text alone, established child role/model/effort/depth, direct-child counts, native leaf behavior, parallel overlap where claimed, and zero grandchildren.
- The runtime record is environment- and scenario-bounded. The real Global target was read-only during acceptance; O2/O3/O4/O5/O6/O7/O9 and controlled Case D used isolated or controlled state where required, while the formal O2/O4/O9 harness verified unchanged protected Global state, zero unexpected observed paths, and zero residual acceptance artifacts. Windows, Ubuntu, and macOS CI remain source validation only.
- Release-preparation Commit `969e2b311df54c43168c4e1bfe5a28661041d50b` and post-release README sync Commit `19221f334be2f0aeb3dd9dc42139f8e2063eeea6` each passed exact-SHA CI on Windows, Ubuntu, and macOS. The immutable setup entry is repinned separately after this reviewed contract commit exists.

## v4.1.0-rc5 (published prerelease)

- Implemented optional canonical ModelDial reference-cost metadata for the API v1 and full-snapshot adapters. Cost validation is fail-soft and selection-neutral; Profile and LKG projection uses the actual selected effort.
- Added receipt-safe `--print-selection` while preserving the RC4 `--print-role` stdout and exit contract, same-day legacy Profile reuse, and legacy LKG compatibility.
- Added one read-only `--status-json` health reader shared by natural-language status and diagnostic UX, with fixed health precedence, exact diagnostic whitelist, symbolic locations, and path/URL/secret sanitization.
- Extended the Global policy with fixed-order delegated Receipt suffixes for reference cost, LKG fallback, and capability degradation, without extra selector, network, state, probe, or child work at Receipt time.
- Added the natural-language latest-version semantic workflow for Stable and prerelease discovery, strict SemVer selection, prerelease notice, immutable tag peeling and movement detection, and exact-commit verification. The installer remains transaction-only and contains no release client or auto-updater.
- Bumped the source installer payload to `v4.1.0-rc5`, retained manifest schema `1`, added optional strict `--source-commit`, true zero-write transaction preflight for `--dry-run`, automatic downgrade refusal, and exact RC4→RC5 fake-home lifecycle coverage.
- RC4→RC5 fake-home apply changes exactly the managed Global `AGENTS.md` block, installed selector, and manifest. Five Luna agents, config, Daily Profile, and LKG remain byte-identical; backup, ownership conflict, second-apply idempotency, and exact rollback are covered.
- Source Commit A is `5ae88ff9190b31174c55a6136c0c8c8611d0b34c`; its Windows, Ubuntu, and macOS source CI passed. The historical RC5 setup contract remains available at immutable documentation commit `ccd9d84da2f74df9ca2d919729b75eebf2dac27a`.
- The documented-environment RC5 O1-O10 record, including O4 and O9, remains bounded evidence. Final O4/O9 re-certification was not obtained due to `CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`; no confirmed product-runtime regression is reported.
- Added `scripts/accept_rc5_runtime_isolation.py` and its regression suite. The final acceptance boundary runs O4 and O9 in an isolated environment, limits the real `CODEX_HOME` to protected-state integrity checks, allows only internal safe `plugins/cache/**` directory reparses, rejects all other symlinks and Windows junctions plus mount points, hardlinks, shared identity, and path escape, and fails closed outside exact Codex platform and local-storage namespaces. O9 is fail-soft observability; RC4→RC5 installer lifecycle validation is separate.
- The earlier Phase A statement “No Source Commit A, immutable RC5 setup pin, tag, release, real Global upgrade, Daily Profile or LKG refresh, Stable promotion, or O1-O10 runtime acceptance has occurred” is superseded by the source, setup-contract, and bounded runtime evidence above. RC5 later became a published Preview and is now historical; RC6 was the final published Preview before Stable promotion.

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

### Post-release Public Beta validation

These records are separate from release-source evidence and do not change the RC4 tag, source, payload, or release gates.

- `DAY_2_CROSS_DAY_END_TO_END_PASS`: recorded Day-2 cross-day end-to-end acceptance passed with `luna_max` ×3, verified parallel overlap, native leaf behavior, and Sol acceptance. The test verified the naturally refreshed current-day result; it did not directly observe the refresh event.
- `DAY_2_SAME_DAY_NEW_SESSION_PERSISTENCE_PASS`: a recorded fresh Codex session reused the same-day cached `luna_max` profile without changing its SHA or mtime and completed three-child parallel delegation with matching Receipt metadata.
- `SELECTOR_URL_EXCEPTION_HARDENING = DEFERRED_TO_PRE_STABLE`: malformed URL parsing exception normalization remains a known pre-stable hardening item. RC4 does not modify the selector for this finding, and the item is not an RC4 Public Beta blocker.

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
