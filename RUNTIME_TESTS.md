# Native Runtime Test Protocol

Status: `v4.1.2 — CURRENT STABLE RELEASE / DEFAULT INSTALLATION TARGET`; `v4.1.1` is the previous immutable Stable, while RC6 and RC5 remain historical Prereleases.

These results describe only the recorded environments and scenarios below. They do not imply runtime validation across every operating system, Codex client, account, or user environment.

## v4.1.3 candidate — source and fake-home evidence

Candidate Source Commit A is
`71894e2ef5007c9ba3e6f9d9efbf91cbdad302b4`. Exact-SHA CI run `33253340074`
passed on Windows, Ubuntu, and macOS and reported `363` tests all `PASS`.
Current-master evidence commit `bafc41b50269a0b65aba64594e850f6171a714ac`
passed CI run `33253429974` on the same three source-validation platforms. The
evidence commit is not Source Commit A and is not an installer source substitute.

Repository fake-home lifecycle tests cover v4.1.2-to-v4.1.3 dry-run, apply,
the selector-plus-manifest ownership boundary, transaction backup,
second-apply idempotency, exact rollback, and modified-owned-selector conflict
with zero writes. Read-only live checks on 2026-08-29 exercised the ModelDial
API v1.1 and Full Snapshot paths independently and confirmed the intended
backend-axis selection and comparable reference-cost projection.

This is repository, fake-home, and read-only network validation only. No real
Global v4.1.3 installer apply, real authentication test, Daily state write, or
candidate fresh-task smoke was performed. The public target remains v4.1.2
until the immutable Setup, Assisted Installation, tag, and non-draft,
non-prerelease Release chain is completed.

`V413_SOURCE_SHA = 71894e2ef5007c9ba3e6f9d9efbf91cbdad302b4`;
`V413_EXACT_SHA_CI = PASS`;
`V413_CURRENT_MASTER_EVIDENCE_CI = PASS`;
`V413_FAKE_HOME_LIFECYCLE = PASS`;
`V413_REAL_GLOBAL_APPLY = NOT_RUN`;
`V413_FRESH_TASK_COMPATIBILITY = NOT_RUN`;
`V413_PUBLIC_RELEASE = NOT_ESTABLISHED`.

## v4.1.2 Stable promotion — setup and runtime evidence

`v4.1.2` is the published Stable release and default public installation target.
Source Commit A is
`551520c2435aca94d60132f292edbd53cc975cbe`. Exact-SHA CI run `32717295801`
passed on Windows, Ubuntu, and macOS and reported `357` tests all `PASS`.
Current-master evidence commit `fac118ac5ca096aaf1ef8d68b79bfc1372998a5a`
passed CI run `32717520585` on the same three source-validation platforms. The
current-master evidence commit is not Source Commit A and is not an installer
source substitute. The immutable Setup anchor is
`4b2a6004fb92b6661166cb73e656cc2888b0a2ef`; the immutable Assisted
Installation anchor is `a130c676fa5924e44034dc8c27f3dc0abfc3bcad`.

The recorded real Global baseline was `v4.1.0-rc6`, source
`50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49`. From a detached exact Source A
checkout, dry-run returned `DRY_RUN_PASS`, `writes NO`, `effective_changes 2`,
and five-effort capability `PASS`. Apply returned `UPGRADED`,
`configuration_preserved true`, `effective_changes 2`, changed only the
selector and install manifest, and created one transaction backup. Second apply
returned `CURRENT_INSTALLATION_PASS`, `writes NO`, `effective_changes 0`, and
`backup NONE`.

Daily selector proof returned a legal role and matching effort; the specific
day's effort is intentionally not recorded. Same-day Profile and LKG were not
rewritten. Exactly one fresh-task compatibility smoke ran for about `169.4`
seconds with `codex-cli 0.146.0`, exited `0`, and passed `CLI`, `Luna
capability`, `Selector`, `Delegation`, `Protected state`, `Runtime contract`,
and final `Compatibility`. Pre/post protected hashes for `AGENTS.md`,
configuration, the five agents, selector, manifest, Profile, LKG, and lock were
unchanged; the smoke created no backup.

This record is limited to one native Windows Codex environment. Windows,
Ubuntu, and macOS CI are source validation only, not three-platform real-runtime
validation. The v4.1.2 GitHub Release is non-draft and non-prerelease, and the
current public README and assisted-installation entry use the immutable anchors
recorded above.

`V412_SOURCE_SHA = 551520c2435aca94d60132f292edbd53cc975cbe`;
`V412_EXACT_SHA_CI = PASS`;
`V412_CURRENT_MASTER_EVIDENCE_CI = PASS`;
`V412_DRY_RUN = DRY_RUN_PASS`;
`V412_APPLY = UPGRADED`;
`V412_SECOND_APPLY = CURRENT_INSTALLATION_PASS`;
`V412_FRESH_TASK_COMPATIBILITY = PASS`;
`V412_PUBLIC_RELEASE = STABLE`.

## v4.1.1 previous immutable Stable — historical promotion evidence

Stable Source Commit A2 is
`ca8e9e4caf5564ffe8d0a11fe376047594f8a748`; its exact-SHA CI passed on
Windows, Ubuntu, and macOS. The installer payload is `v4.1.1` with manifest
schema `1`.

- `v4.1.0` -> `v4.1.1` fake-home lifecycle coverage changes only
  `sol-luna-v4/install-manifest.json` and byte-preserves the selector, Global
  policy, five Luna agents, config, Daily Profile, and LKG.
- Local coverage verifies dry-run zero writes, transaction backup,
  second-apply idempotency, exact rollback, downgrade refusal, and ownership
  conflict fail-closed behavior.
- After explicit Daily selection initialization, an independent one-run
  pre-publication fresh-task compatibility smoke exited `0` after about 144.2
  seconds and passed `CLI`, `Luna capability`, `Selector`, `Delegation`,
  `Protected state`, `Runtime contract`, and final `Compatibility` checks
  against the unchanged installed product runtime.
- No real Global `v4.1.1` apply was performed. The Stable promotion reuses the
  separately accepted product payload and changes only installed manifest
  version/source metadata.
- `V410_TO_V411_INSTALLED_BEHAVIOR_CHANGED = NO`;
  `ACCEPTANCE_CONTRACT_CHANGED = YES`.

This promotion evidence does not broaden RC6's recorded runtime scope or imply
real-runtime validation on all three CI platforms, every Codex client, every
account, or every user environment. Stable publication remains a separate
immutable tag and non-draft, non-prerelease GitHub Release fact.

`V411_SOURCE_COMMIT_CREATED = YES`;
`V411_SOURCE_SHA = ca8e9e4caf5564ffe8d0a11fe376047594f8a748`;
`V411_EXACT_SHA_CI = PASS`;
`V411_FRESH_TASK_COMPATIBILITY = PASS`.

## v4.1.0-rc6 historical Preview — recorded fresh-task runtime acceptance

RC6 Source Commit A is
`50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49`; exact-SHA CI passed on Windows,
Ubuntu, and macOS. The installer payload is `v4.1.0-rc6` with manifest schema
`1`. RC6 remains an immutable historical GitHub Prerelease / Preview / Public
Beta. Its reviewed setup contract remains pinned through an exact immutable
documentation commit that is distinct from Source Commit A.

- RC5 -> RC6 fake-home lifecycle coverage expects only
  `sol-luna-v4/selector.py` and `sol-luna-v4/install-manifest.json` to change;
  local tests cover idempotency, backup, exact rollback, and ownership
  fail-closed behavior.
- The selector normalizes malformed URL parsing, hostname, and port `ValueError`
  cases to `SnapshotInvalid`, preserving the API -> snapshot -> LKG ->
  fail-closed source order.
- Compatibility-smoke baseline coverage uses dual exact rollout roots and
  bounded writer-settle/fail-closed evidence. The harness does not modify
  product runtime.
- `PRODUCT_RUNTIME_CHANGED = YES`; `ACCEPTANCE_CONTRACT_CHANGED = YES`.
- The separately authorized real RC5 -> RC6 Global upgrade is recorded `PASS`
  in one native Windows Codex environment. It returned `UPGRADED`, changed only
  the installed selector and ownership manifest, and was followed by a
  zero-write `IDEMPOTENT_PASS`. The installer-owned rollback snapshot exists
  under the owned backup root and its recorded hashes verify.
- Compatibility smoke, O1-O10 acceptance, Final O4/O9 re-certification, and
  Runtime Cases A/B/C/D are recorded `PASS` in the documented environment.
  This is not three-platform real-runtime validation, a universal compatibility
  claim, or standalone Stable evidence. RC6 publication is a separate immutable
  tag and historical Prerelease fact.

- O1 Natural-language healthy status — `PASS`
- O2 No-profile healthy status — `PASS`
- O3 Degraded LKG Receipt and status — `PASS`
- O4 Capability-degraded selected-effort Receipt and status — `PASS`
- O5 Unavailable evidence status — `PASS`
- O6 Misconfigured precedence — `PASS`
- O7 Safe diagnostic report — `PASS`
- O8 Latest prerelease immutable discovery and notice — `PASS`
- O9 Fail-soft observability selection, status, and Receipt omission — `PASS`
- O10 Fresh-session delegation and Receipt suffixes — `PASS`

### RC6 evidence boundary

- The installed manifest reported `v4.1.0-rc6`, schema `1`, and Source Commit A.
  The installed selector was byte-identical to Source Commit A; five Luna agent
  payloads, native-leaf settings, Global policy, and managed config validated.
- The compatibility smoke passed CLI, Luna capability, selector, delegation,
  protected-state, and runtime-contract checks. It remained a separate baseline
  and was not used as a substitute for O1-O10.
- The formal O2/O4/O9 harness installed Source Commit A into an independent fake
  `CODEX_HOME`, copied authentication to a distinct file identity, redirected
  home/application-data/temp/XDG paths, and verified actual parent and direct
  child rollout metadata. O2 used one native Luna child; O4 selected the bounded
  capability-degraded effort; O9 preserved selection while omitting invalid or
  missing ref-cost metadata and classified profile read failure as
  `Misconfigured / DAILY_PROFILE_READ_FAILED`.
- Final O4/O9 re-certification passed. Across O2/O4/O9, the real protected
  Sol/Luna inventory and root identity were unchanged, observed unknown paths
  were zero, isolated runtime paths were fully classified within the documented
  snapshot boundary, and owned acceptance artifacts had zero residuals.
- O3 ran a separate isolated LKG case with one completed native Luna child,
  depth `1`, zero grandchildren, matching role/model/effort metadata, a
  `Degraded / LKG_FALLBACK_ACTIVE` status, and an `LKG` Receipt suffix derived
  from the saved selection. Receipt generation added no selector, network, or
  state work.
- O5 and controlled Case D used isolated state. Case D produced
  `NO_LUNA_PROFILE_AVAILABLE` with parent-visible evidence; removing that
  evidence forbade `Luna unavailable`. The real selector, state, account, and
  Global configuration were not damaged or reconfigured.
- O8 enumerated all published Releases, accepted only non-draft strict SemVer
  entries with matching prerelease flags, selected the then-current RC5
  prerelease, and read its tag twice to the same peeled commit. Because the
  installed RC6 was newer, the workflow performed no downgrade, write, or
  backup.
- Runtime Case A completed with zero children and the reasoning/architecture
  Receipt. Runtime Case B used two actual direct Luna children with verified
  overlap and zero grandchildren. Runtime Case C used read-only sequential work,
  zero children, no selector, and no availability evidence. Controlled Case D
  verified both positive and negative availability-evidence gates.
- Parent-visible rollout metadata, not Receipt text alone, established child
  presence or absence, role/model/effort/depth, direct-child count, leaf behavior,
  overlap where claimed, completion, and descendant count. Sol performed final
  acceptance.

## v4.1.0-rc5 historical Preview — bounded documented-environment O1-O10 record

RC5 `Observability & UX` Source Commit A is
`5ae88ff9190b31174c55a6136c0c8c8611d0b34c`. Its historical immutable setup
contract is available at documentation commit
`ccd9d84da2f74df9ca2d919729b75eebf2dac27a`. The documented-environment RC5
O1-O10 record below is bounded evidence from one recorded Codex environment;
it is not a final O4/O9 re-certification or a universal runtime claim.

- O1 Natural-language healthy status — `PASS`
- O2 No-profile healthy status — `PASS`
- O3 Degraded LKG Receipt and status — `PASS`
- O4 Capability-degraded selected-effort Receipt and status — `PASS`
- O5 Unavailable evidence status — `PASS`
- O6 Misconfigured precedence — `PASS`
- O7 Safe diagnostic report — `PASS`
- O8 Latest prerelease immutable discovery and notice — `PASS`
- O9 Fail-soft observability selection, status, and Receipt omission — `PASS`
- O10 Fresh-session delegation and Receipt suffixes — `PASS`

RC4→RC5 fake-home installer lifecycle validation is a separate recorded
`PASS` and has no O-number. RC5 real Global upgrade, idempotency, and rollback
readiness remain a separately authorized operation and are `NOT RUN`. Final
O4/O9 re-certification was not obtained due to
`CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`; no confirmed product-runtime
regression is reported.

`RC5_SOURCE_COMMIT_CREATED = YES`;
`RC5_SOURCE_SHA = 5ae88ff9190b31174c55a6136c0c8c8611d0b34c`;
`RC5_SETUP_CONTRACT_COMMIT = ccd9d84da2f74df9ca2d919729b75eebf2dac27a`;
`RC5_RUNTIME_ACCEPTANCE_COMPLETED = YES`;
`RC5_RUNTIME_CATEGORY_MODEL_FIXED = YES`.

`RC6_SOURCE_COMMIT_CREATED = YES`;
`RC6_SOURCE_SHA = 50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49`;
`RC6_SETUP_CONTRACT_REVIEWED = YES`;
`RC6_RUNTIME_ACCEPTANCE_COMPLETED = YES`;
`RC6_FINAL_O4_O9_RECERTIFICATION = PASS`;
`RC6_REAL_GLOBAL_UPGRADE = PASS`.

For the historical RC5 acceptance-boundary record, the product runtime payload
was frozen at
`src/selector.py`, `scripts/install.py`, `templates/AGENTS.global.md`, and
`.codex/agents/*`. This file, `CODEX_SOL_LUNA_SETUP.md`, `ARCHITECTURE.md`, and
`SECURITY.md` are the acceptance contract and may track acceptance redesigns.
`PRODUCT_RUNTIME_CHANGED = NO`; `ACCEPTANCE_CONTRACT_CHANGED = YES`.

The committed repeatable harness runs O2, O4, and O9 from Source Commit A under
a unique owned acceptance root. O4 and O9 execute with an isolated
`CODEX_HOME`, home/profile, application-data, temporary-storage, and XDG
environment. The harness constructs one `isolated_runtime_env`; selector
subprocesses, `codex exec`, installer and repository subprocesses receive it
explicitly, while in-process O9 fail-soft and status/health checks run under
that same environment with the caller environment restored afterward. No
O4/O9 path inherits the real process environment. Before any installer write
or credential copy, the harness
validates that the acceptance root is outside the real runtime, is not a
user-controlled symlink, junction, reparse point, or mount, and contains no
hardlink into the real runtime. The fixed macOS `/var` system alias is
recognized so canonical platform temp directories remain usable. A per-run
ownership marker, token, and directory identity gate cleanup; cleanup removes
reparse entries without traversing them and fails closed if ownership or
identity changes.

The real `CODEX_HOME` is used only for pre/post protected-state integrity and
root-identity verification. Managed Sol/Luna policy, configuration, agents,
selector, manifest, and the complete `sol-luna-v4/state/**` tree must remain
unchanged. The state inventory covers the Daily Profile, LKG, `selector.lock`,
and every other state entry; before/after hash, object type, device/file
identity, link count, and reparse status are compared. Unrelated real-home
runtime activity is not an RC5 runtime-attribution source and does not fail
acceptance.

Runtime attribution is confined to the isolated home. The existing explicit
Codex session, session-index, app-cache, and active-exec namespaces remain
narrowly allowlisted. `CODEX_PLATFORM_RUNTIME_STATE` additionally accepts only
the exact root-level `.sandbox_migration` safe regular file, safe ordinary
objects under the exact `skills/**` and
`plugins/.remote-plugin-install-staging/**` trees, structurally valid entries
under `browser/sessions/**`, `cache/remote_plugin_catalog/**`,
`plugins/cache/**`, `tmp/arg0/**`, and a validated runtime subtree under
`visualizations/`; their broader parent trees are not allowlisted. A normal
remote-plugin install clears staging descendants but may retain the empty exact
staging root, so the contract does not require that root to disappear. An
internal `plugins/cache/**` directory reparse is allowed only when its resolved
target remains inside both the isolated `CODEX_HOME` and plugin-cache
namespace, does not overlap protected state, and does not loop. Reparses are
not allowed in the new staging or skills trees.
Root SQLite storage is restricted to the `goals`, `logs`, `memories`, `queue`,
`state`, and `thread_history` ID families with `-wal` and `-shm` sidecars coupled
to a safe base. Global `*.sqlite` and `*.db` suffix rules are forbidden.

Any isolated-home reparse escape, unexpected hardlink, invalid runtime type,
change to protected real state, or write outside the exact isolated runtime
categories fails the harness.
Authentication bytes are copied only to the isolated fake home with a distinct
file identity; they are not committed, printed, or included in the result. The
Codex child receives a fixed minimal inherited environment plus fake-home
values for home, application data, temporary storage, and XDG roots, so
unrelated user credential variables are not forwarded. All real, fake,
temporary, repository, and executable paths are symbolized before the JSON
evidence is printed; remaining user-home path shapes and credential-shaped
values are redacted.

This is environment- and scenario-bounded evidence for the published RC5
Preview. It is not three-platform real-runtime validation, a tag, a Stable
claim, or a Stable promotion. Windows, Ubuntu, and macOS CI remain source
validation only.

`SELECTOR_URL_EXCEPTION_HARDENING = DEFERRED_TO_PRE_STABLE` describes the RC5
record; the published RC6 Preview implements this normalization.

Native Runtime Tests 1-5 passed in fresh project sessions after the project custom-agent configuration and `AGENTS.md` policy were loaded. This document records generic results only; it intentionally omits session IDs, usernames, absolute paths, rollout IDs, and installation IDs.

Static validation and Native Runtime validation remain separate gates. The runtime tests do not grant Luna planning, architecture, orchestration, or final-acceptance authority. Sol owns those responsibilities.

## v4.1.0-rc4 published prerelease — Receipt reason evidence-gating

RC4 fixes one policy classification defect: without current-task parent-visible Luna availability failure evidence, a Sol-only Receipt must not report `Luna unavailable`. The five-outcome taxonomy and delegation threshold are unchanged. Receipt generation remains decision-neutral and must not create evidence through selector invocation, capability probes, tools, children, network access, state, telemetry, or repository writes.

- Source validation commit `95cfd53200a3fc53b50a48fe7ab251dcc6d5e00b`: Windows, Ubuntu, and macOS `PASS`; full repository suite `114/114 PASS`.
- Final source pin `d17bea49fdb0710bb2101f1577045bed2477ff79`: Windows, Ubuntu, and macOS `PASS`.
- RC3→RC4 fake-home lifecycle: upgrade, backup, idempotency, exact rollback, and ownership-conflict fail-closed `PASS`.
- Frozen selector, five Luna agents, config, state schema, Daily Profile, and LKG: unchanged by the RC4 payload.

### Real RC3 → RC4 Global upgrade — `PASS`

- Result: `UPGRADED`; effective changes: `2`.
- Only the managed Global `AGENTS.md` block and install manifest changed.
- Selector, five Luna agents, Global config, Daily Profile, and LKG remained unchanged.
- A second apply returned `IDEMPOTENT_PASS`.
- Rollback readiness passed.

### Runtime Case A — `PASS`

- Actual direct-child count: `0`.
- Final line: `Sol/Luna: Sol-only · reasoning/architecture task`.

### Runtime Case B — `PASS`

- Selected role: `luna_max`; actual direct children: `3`.
- Child model: `gpt-5.6-luna` ×3; effort: `max` ×3.
- Parallel overlap: verified; grandchildren: `0`.
- Final line: `Sol/Luna: delegated · luna_max ×3 · parallel`.

### Runtime Case C — `PASS`

- Selector invoked: `NO`; delegation attempted: `NO`.
- Availability evidence: `NONE`; actual direct-child count: `0`.
- Final line: `Sol/Luna: Sol-only · no independent bounded work`.
- This is the direct regression for the RC3 misclassification: without availability evidence, `Luna unavailable` is forbidden.

### Runtime Case D — controlled / isolated — `PASS`

- Selector result: `NO_LUNA_PROFILE_AVAILABLE`; availability evidence: `PRESENT`.
- With genuine parent-visible availability evidence, `Luna unavailable` is allowed.
- Negative control: availability evidence `NONE`; `Luna unavailable` is forbidden.
- The controlled case did not modify the real `.codex` environment.

The recorded RC4 runtime evidence applies only to the environments in which it was observed. It is not three-platform real Codex runtime validation and does not claim validation for every operating system, client, account, or user.

### Additional recorded Public Beta runtime evidence

These records were obtained after the RC4 release source and tag were fixed. They are post-release Public Beta evidence, not release-source evidence, a new release gate, a tag change, or a Stable promotion.

#### Day-2 cross-day end-to-end — `PASS`

- Status: `DAY_2_CROSS_DAY_END_TO_END_PASS`.
- Beijing date: `2026-08-14`; installed version: `v4.1.0-rc4`.
- Today's profile already existed when this test began. It had refreshed naturally from the prior-day recorded state before the test, and the normal delegation path reused the same-day cache.
- `CROSS_DAY_REFRESH_OCCURRED_NATURALLY = YES`.
- `CURRENT_TEST_OBSERVED_REFRESH_EVENT_DIRECTLY = NO`.
- `CURRENT_TEST_VERIFIED_REFRESH_RESULT = YES`.
- Today's role: `luna_max`; source: `modeldial_api_v1`.
- Actual direct children: `3`; agent: `luna_max` ×3; model: `gpt-5.6-luna` ×3; effort: `max` ×3.
- Parallel overlap: verified; grandchildren: `0`; native leaf: `PASS`; Sol acceptance: `PASS`.
- The Receipt matched the actual role, direct-child count, and parallel runtime metadata.
- The repository and installed runtime payload were unchanged by the test.

#### Day-2 new-session same-day persistence — `PASS`

- Status: `DAY_2_SAME_DAY_NEW_SESSION_PERSISTENCE_PASS`.
- Fresh Codex session: `YES`; Beijing date: `2026-08-14`.
- Existing profile role: `luna_max`; effort: `max`; source: `modeldial_api_v1`.
- Normal-path selector calls: `1`; acquisition: `same-day cache`.
- Profile SHA before and after: unchanged; profile mtime before and after: unchanged; LKG: unchanged; profile regenerated: `NO`.
- Actual direct children: `3`; agent: `luna_max` ×3; model: `gpt-5.6-luna` ×3; effort: `max` ×3.
- Parallel overlap: verified; grandchildren: `0`; native leaf: `PASS`; Sol acceptance: `PASS`.
- The Receipt role, direct-child count, and parallel marker all matched the runtime metadata.
- This demonstrates that the recorded same-day persisted profile survived a completely new Codex session. It does not establish universal persistence across all Codex clients or user environments.

### Historical RC4 pre-stable hardening record

`SELECTOR_URL_EXCEPTION_HARDENING = DEFERRED_TO_PRE_STABLE`

Malformed port or malformed IPv6-style URL input could surface a `ValueError` without unified normalization in RC4. RC6 resolved this item by normalizing those URL parsing, hostname, and port cases to `SnapshotInvalid`; Stable preserves that fix unchanged.

## v4.1.0-rc3 real upgrade and Receipt acceptance — `PASS`

The published RC3 prerelease passed its separately authorized real upgrade and fresh-session Receipt acceptance in one recorded Codex environment. The full repository suite passed `109/109`, and Windows, Ubuntu, and macOS CI passed for the release source.

### Real RC1 → RC3 Global upgrade — `PASS`

- Result: `UPGRADED`; effective changes: `2`.
- The managed Global `AGENTS.md` block and install manifest changed.
- Selector, five Luna agents, Global config, selector state and schema, Daily Profile, and LKG remained unchanged.
- A second apply returned `IDEMPOTENT_PASS`.
- Rollback readiness passed.

### Sol-only Receipt — `PASS`

- Actual direct-child count: `0`.
- Final line: `Sol/Luna: Sol-only · reasoning/architecture task`.

### Delegated Receipt — `PASS`

- Selected role: `luna_max`; actual direct children: `3`.
- Child model: `gpt-5.6-luna` ×3; effort: `max` ×3.
- Parallel overlap: verified; grandchildren: `0`.
- Final line: `Sol/Luna: delegated · luna_max ×3 · parallel`.

In both Receipt cases, parent-visible runtime metadata established child absence or presence. Receipt text remains a user-facing execution summary and is not runtime attestation by itself. Native leaf, parallel delegation, and Sol Acceptance all passed.

## Safety boundary

- The tests use a fresh project session and the current Beijing-date Daily Profile.
- Routine test runs do not alter global Codex configuration, global agents, Hooks, or environment variables.
- Installer lifecycle tests write only to explicit fake homes. Separately approved real global upgrades and fresh-session runtime acceptance were recorded for the stable source, RC3, and RC4 prereleases without widening routine repository-test permissions.

## Test results

### Test 1: project custom-agent discovery — `PASS`

The fresh project session discovered all five formal native custom Luna agents, including the canonical role names. No runtime identifier is recorded here.

### Test 2: explicit native spawn — `PASS`

A named native custom agent ran as GPT-5.6 Luna at its configured selected effort and returned the required test sentinel. The result confirms native `agent_type`/custom-agent spawning; it does not establish a direct model override path.

### Test 3: `AGENTS.md` policy delegation — `PASS`

Sol read the current Daily Profile, delegated the bounded read-heavy task to its `selected_role`, and performed the final acceptance. The role was selected by policy rather than by a Hook Router, registry, or direct model override.

### Test 4: native leaf — `PASS`

Each formal Luna custom agent loads `[agents] enabled = false`. The child tool surface contains no multi-agent or delegation tools, so the native leaf boundary is enforced. Luna remains a bounded execution worker.

### Test 5: parallel native delegation — `PASS`

Two independent bounded read-only checks were delegated according to the current policy, both used the selected role, stayed within the project concurrency limit, and were consolidated and accepted by Sol.

## Global Runtime results

- G1 Global Discovery — `PASS`
- G2 Selector + Explicit Luna — `PASS`
- G3 Automatic Delegation — `PASS`
- G4 Native Leaf — `PASS`
- G5 Native Parallel — `PASS`
- G6 Sol Acceptance — `PASS`
- G7 Legacy Absence — `PASS`

Daily Selector same-day cache reuse and no-`ultra` checks passed. LKG and fail-closed behavior are validated by the test suite. The global record is generic and contains no machine- or session-specific identifiers.

## Result rule

Native Runtime Tests 1-5 and Global Runtime G1-G7 provide the generic runtime evidence for stable `v4.0.0` in the tested Codex Desktop/App Server environment. The RC3 and RC4 upgrade and Receipt results above apply only to the recorded environments in which they were observed. They do not promise compatibility with future Codex versions or establish real runtime PASS for every operating system, client, account, or user.
