# Native Runtime Test Protocol

Status: `v4.1.0-rc4 — PUBLISHED PRERELEASE / CURRENT PREVIEW / RUNTIME ACCEPTANCE PASS`; `v4.0.0 — STABLE`

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
