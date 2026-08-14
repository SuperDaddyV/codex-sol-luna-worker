# Native Runtime Test Protocol

Status: `v4.1.0-rc4 — PUBLISHED PRERELEASE / CURRENT PREVIEW / RECORDED RUNTIME ACCEPTANCE — PASS`; `v4.0.0 — STABLE`

These results describe only the recorded environments and scenarios below. They do not imply runtime validation across every operating system, Codex client, account, or user environment.

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

### Known pre-stable hardening item

`SELECTOR_URL_EXCEPTION_HARDENING = DEFERRED_TO_PRE_STABLE`

Malformed port or malformed IPv6-style URL input may surface a `ValueError` without unified normalization. RC4 does not modify the selector for this finding. It is not an RC4 Public Beta blocker, but it remains a pre-stable hardening item that must be revisited before Stable promotion.

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
