# Changelog

## v4.1.4 (published Stable release)

- Verifies the uninstall transaction backup before modifying any managed path,
  matching the documented safety contract already enforced by installation.
- Routes every exception raised after uninstall backup verification through
  exact rollback before preserving the original stable installer error. This
  closes the gap where a path-safety `InstallerError` could bypass rollback
  after an earlier uninstall operation had already completed.
- Adds regression coverage proving that backup verification failure preserves
  the exact installed tree and that an exception after one effective uninstall
  operation restores the exact pre-uninstall tree.
- Advances the installer and ModelDial User-Agent to `v4.1.4`. The directly
  validated v4.1.3-to-v4.1.4 fake-home upgrade changes only
  `sol-luna-v4/selector.py` and `sol-luna-v4/install-manifest.json`, remains
  idempotent on second apply, rolls back exactly, and fails closed when the
  previously owned selector was modified.
- Stable Source Commit A
  `6a537b445ad6f17a9600c05e655f51a2844bfcc8` passed exact-SHA CI run
  `33264634602` on Windows, Ubuntu, and macOS with `366` tests all `PASS`.
  This is repository source validation only; it does not establish a real
  Global install, authentication result, fresh-task runtime result, tag, or
  Release.
- The immutable Setup and Assisted Installation anchors are
  `bf01c438eae66f5ef9a27d401c6ee845f89d5d59` and
  `5e1ce80d3ed444834f700ac0154bfe444dec8cd3`; neither documentation commit is
  the runtime source. The annotated `v4.1.4` tag and non-draft,
  non-prerelease GitHub Release establish Stable publication.
- No real Global v4.1.4 installer apply, authentication test, Daily state
  write, or fresh-task compatibility smoke is claimed.

## v4.1.3 (published Stable release)

- Accepts ModelDial API schemas `1.0` and `1.1` while preserving the v4.1
  backend-score contract. Schema `1.1` requires `defaultRanking =
  overallRankings`, consumes only the backward-compatible `rankings` backend
  axis, and rejects canonical rows whose `scoreBasis`, `score`, and
  `backendScore` do not identify the same backend result.
- Restores optional Full Snapshot reference-cost comparison after ModelDial
  moved provider and route identity to
  `model_configuration.provider_id` and
  `model_configuration.route_type`. Cost metadata remains fail-soft and cannot
  affect role selection.
- Restricts Full Snapshot Luna score selection to the `codex` /
  `official_login` route with first-party-controlled score and route
  provenance, preventing a future cross-provider or cross-route row from
  entering the five-effort selector contract.
- Adds a sanitized schema `1.1` fixture, backend-versus-overall regression
  coverage, malformed score-basis cases, API-to-snapshot fallback coverage,
  installer version/User-Agent synchronization, and v4.1.2-to-v4.1.3
  fake-home upgrade, ownership, idempotency, backup, and exact rollback tests.
- Changes no overall-ranking adoption, Agent Profile integration, winner or
  tie-break algorithm, Daily Profile or LKG schema, agent payload, Global
  policy, config, concurrency, installer manifest schema, migration behavior,
  release resolver, or real Global runtime state.
- Stable Source Commit A
  `71894e2ef5007c9ba3e6f9d9efbf91cbdad302b4` passed exact-SHA CI run
  `33253340074` on Windows, Ubuntu, and macOS with `363` tests all `PASS`.
  This is repository source validation only; it does not establish a real
  Global install, real authentication, runtime acceptance, tag, or Release.
  Current-master evidence commit
  `bafc41b50269a0b65aba64594e850f6171a714ac` passed CI run `33253429974` on
  the same three source-validation platforms. The immutable Setup and Assisted
  Installation anchors are `5c29abc9aed340f4a7c45c22a0f8b36242b920bb` and
  `23eeba1a5fb21e0483f4140aeca18b483f3e85bf`; neither is the runtime source.
  The annotated `v4.1.3` tag and non-draft, non-prerelease GitHub Release
  establish Stable publication. The public bilingual README uses the same
  immutable chain.

## v4.1.2 (published Stable release)

- Rejects filesystem aliases inside installer-owned paths while preserving the
  established cross-platform `BACKUP_FAILED` result when an ordinary file
  blocks backup creation.
- Adds one reusable least-privilege child-environment builder for production
  Codex, Python, Git, and approved package-manager subprocesses. Unrelated
  ambient variables are excluded; explicit runtime, authentication, workload
  identity, proxy, certificate, and `CODEX_HOME` requirements remain available
  only to the child purposes that need them.
- Preserves selected custom-provider and enabled MCP environment names declared
  by `CODEX_HOME/config.toml`. Invalid configuration, provider `auth.command`,
  unsafe external SQLite homes, and configuration aliases fail closed instead
  of restoring full ambient inheritance.
- Tightens same-day Daily Profile reuse and compatibility-smoke selector status
  reason-code validation without changing the five Luna efforts or selection
  algorithm.
- Promotes Source Commit A
  `551520c2435aca94d60132f292edbd53cc975cbe` as the v4.1.2 Stable runtime
  source. Exact-SHA CI run `32717295801` passed on Windows, Ubuntu, and macOS
  with `357` tests all `PASS`; this is source validation and does not imply
  three-platform real-runtime validation.
- The current-master evidence commit
  `fac118ac5ca096aaf1ef8d68b79bfc1372998a5a` passed CI run `32717520585` on
  Windows, Ubuntu, and macOS; it is current-tip evidence, not a replacement for
  Source Commit A. The exact Source-A run reported `357` tests all `PASS`.
- Pins the Stable Setup contract at immutable documentation Commit
  `4b2a6004fb92b6661166cb73e656cc2888b0a2ef` and the Assisted Installation
  contract at immutable documentation Commit
  `a130c676fa5924e44034dc8c27f3dc0abfc3bcad`. Neither documentation anchor is
  the runtime source or a mutable branch.
- The recorded real Global baseline was `v4.1.0-rc6`, source
  `50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49`. Detached exact-Source-A dry-run
  returned `DRY_RUN_PASS`, `writes NO`, `effective_changes 2`, and five-effort
  capability `PASS`. Apply returned `UPGRADED`,
  `configuration_preserved true`, `effective_changes 2`, changed only the
  selector and install manifest, and created one transaction backup. Second
  apply returned `CURRENT_INSTALLATION_PASS`, `writes NO`,
  `effective_changes 0`, and `backup NONE`.
- Daily proof returned a legal role and matching effort without recording the
  day's specific effort; same-day Profile and LKG were not rewritten. Exactly
  one fresh-task compatibility smoke ran for about `169.4` seconds with
  `codex-cli 0.146.0`, exited `0`, and passed `CLI`, `Luna capability`,
  `Selector`, `Delegation`, `Protected state`, `Runtime contract`, and final
  `Compatibility`. Protected hashes for `AGENTS.md`, configuration, five
  agents, selector, manifest, Profile, LKG, and lock were unchanged, and the
  smoke created no backup.
- This evidence is limited to one native Windows Codex environment. Windows,
  Ubuntu, and macOS CI are source validation only, not three-platform
  real-runtime validation. The v4.1.2 GitHub Release is the non-draft,
  non-prerelease Stable publication, and its README and assisted-installation
  entries use the immutable documentation anchors above.

## v4.1.1 (previous immutable Stable release)

- Added Stable Source Commit A2
  `ca8e9e4caf5564ffe8d0a11fe376047594f8a748`; 332 local tests and exact-SHA CI
  passed on Windows, Ubuntu, and macOS for both the source branch run and the
  exact `master` run.
- Added a standard-library deterministic installation assistant with explicit
  check, recovery-plan, exact-plan approval, capability-precheck, installer
  handoff, installed-version fast path, result-card, and sanitized support-report
  contracts. The existing transactional installer remains the sole writer and
  rollback authority.
- Added a validated official-source recovery catalog for WinGet on Windows,
  Homebrew on macOS, and APT Git recovery on Ubuntu/Debian. Codex authentication,
  Linux Python-version selection, unsupported package managers, proxy,
  certificate, firewall, and organization-policy cases remain guided user
  actions. P3 standalone bootstrap remains out of scope.
- Advanced only the installer ownership-manifest version from `v4.1.0` to
  `v4.1.1`; selector, policy, agents, config, and selector state are
  byte-preserved by the fake-home lifecycle gate.
- Added an explicit post-reload `SELECTOR_INITIALIZATION` gate to the Stable
  assistant. Both applied and same-version idempotent paths now require the
  canonical `--ensure-daily --print-selection` role/effort proof before a
  separate fresh-task compatibility smoke. The smoke remains read-only and
  never initializes or retries Daily selection.
- Recorded the independent fresh-task compatibility smoke as a one-run `PASS`:
  exit `0` after about 144.2 seconds, with `CLI`, `Luna capability`, `Selector`,
  `Delegation`, `Protected state`, `Runtime contract`, and final
  `Compatibility` all explicit `PASS`. No real Global `v4.1.1` installer apply
  was performed.
- Anchored the reviewed Stable setup and evidence contract at immutable Commit
  `d4a044a04df509285ef38c6afc28b5a68a48a0f9` around Source Commit A2. The
  immutable assisted-installation contract at Commit
  `17eb1d370929e884f91c5f1920a2e0868ce4a421` pins that setup contract, and the
  bilingual README pins both layers; no commit self-references its own SHA.
- Preserved the published `v4.1.0` Stable tag and Release and the annotated
  `v4.1.0-rc6` tag and historical Prerelease unchanged.

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
