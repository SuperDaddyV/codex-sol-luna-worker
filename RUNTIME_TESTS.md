# Native Runtime Test Protocol

Status: `v4.0.0 — STABLE / GLOBAL V4 RUNTIME PASS`

Native Runtime Tests 1-5 passed in fresh project sessions after the project custom-agent configuration and `AGENTS.md` policy were loaded. This document records generic results only; it intentionally omits session IDs, usernames, absolute paths, rollout IDs, and installation IDs.

Static validation and Native Runtime validation remain separate gates. The runtime tests do not grant Luna planning, architecture, orchestration, or final-acceptance authority. Sol owns those responsibilities.

## v4.1.0-rc3 planned Receipt acceptance — `NOT RUN`

RC3 changes the installer-managed Global `AGENTS.md` payload. Its runtime acceptance is intentionally pending until a separately authorized real upgrade and fresh task:

- Case A: use a non-trivial architecture or reasoning task. Require zero direct Luna children and the final line `Sol/Luna: Sol-only · reasoning/architecture task`.
- Case B: use two or three independent bounded read-only checks. Require actual Luna direct children and `Sol/Luna: delegated · <role> ×<direct_child_count>` matching the actual selected role and actual total direct-child count. Accept ` · parallel` only when parent-visible evidence proves at least two children overlapped. Confirm native custom-agent routing without a direct model or reasoning-effort override, and require Sol to review the child evidence and own the final conclusion.

In both cases, inspect parent-visible runtime metadata for child absence or presence. Receipt text is a user-facing execution summary and cannot establish PASS by itself. No RC3 Receipt runtime PASS is claimed in this document.

## Safety boundary

- The tests use a fresh project session and the current Beijing-date Daily Profile.
- Routine test runs do not alter global Codex configuration, global agents, Hooks, or environment variables.
- Installer lifecycle tests write only to explicit fake homes. The separately approved real global migration and isolated no-project Global Runtime acceptance were completed before stable source promotion.

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

Native Runtime Tests 1-5 and Global Runtime G1-G7 provide the generic runtime evidence for stable `v4.0.0` in the tested Codex Desktop/App Server environment. They do not promise compatibility with future Codex versions.
