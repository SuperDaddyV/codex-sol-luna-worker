# Native Runtime Test Protocol

Status: `v4.1.0-rc4 — SOURCE CANDIDATE / STATIC PASS / FRESH RUNTIME NOT RUN`; `v4.1.0-rc3 — CURRENT PUBLISHED PREVIEW`; `v4.0.0 — STABLE`

Native Runtime Tests 1-5 passed in fresh project sessions after the project custom-agent configuration and `AGENTS.md` policy were loaded. This document records generic results only; it intentionally omits session IDs, usernames, absolute paths, rollout IDs, and installation IDs.

Static validation and Native Runtime validation remain separate gates. The runtime tests do not grant Luna planning, architecture, orchestration, or final-acceptance authority. Sol owns those responsibilities.

## v4.1.0-rc4 source candidate — Receipt reason evidence-gating

The RC4 source candidate fixes one policy classification defect: without current-task parent-visible Luna availability failure evidence, a Sol-only Receipt must not report `Luna unavailable`. The five-outcome taxonomy and delegation threshold are unchanged. Receipt generation remains decision-neutral and must not create evidence through selector invocation, capability probes, tools, children, network access, state, telemetry, or repository writes.

- Repository suite: `114/114 PASS`.
- RC3→RC4 fake-home lifecycle: upgrade, backup, idempotency, exact rollback, and ownership-conflict fail-closed `PASS`.
- Frozen selector, five Luna agents, config, state schema, Daily Profile, and LKG: unchanged by the candidate payload.
- Fresh-session runtime smoke — `NOT RUN`.

### Planned RC4 runtime acceptance

- Runtime Case A — reasoning: require `Sol/Luna: Sol-only · reasoning/architecture task` and zero direct children.
- Runtime Case B — delegated: require actual delegated child metadata; role, direct-child count, and optional `parallel` must match parent-visible facts.
- Runtime Case C — no-independent-work: use a non-trivial, non-architecture, sequential or tightly coupled task with no availability failure evidence and zero children. The selector may run only when normal execution requires it. Require `Sol/Luna: Sol-only · no independent bounded work`; forbid `Luna unavailable`.
- Runtime Case D — real-unavailable-evidence: use a controlled fixture, fake `CODEX_HOME`, test harness, or non-production simulation where normal execution already exposed the failure. Do not break the real selector, state, account, or Global environment to manufacture evidence.

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
- Installer lifecycle tests write only to explicit fake homes. Separately approved real global upgrades and fresh-session runtime acceptance were recorded for the stable source and RC3 prerelease without widening routine repository-test permissions.

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

Native Runtime Tests 1-5 and Global Runtime G1-G7 provide the generic runtime evidence for stable `v4.0.0` in the tested Codex Desktop/App Server environment. The RC3 upgrade and Receipt results above apply only to the one recorded Codex environment in which they were observed. They do not promise compatibility with future Codex versions or establish real runtime PASS for every operating system, client, account, or user.
