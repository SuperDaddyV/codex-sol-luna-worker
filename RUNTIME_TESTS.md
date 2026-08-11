# Native Runtime Test Protocol

Status: `v4.0.0-rc1 — PASS`

Native Runtime Tests 1-5 passed in fresh project sessions after the project custom-agent configuration and `AGENTS.md` policy were loaded. This document records generic results only; it intentionally omits session IDs, usernames, absolute paths, rollout IDs, and installation IDs.

Static validation and Native Runtime validation remain separate gates. The runtime tests do not grant Luna planning, architecture, orchestration, or final-acceptance authority. Sol owns those responsibilities.

## Safety boundary

- The tests use a fresh project session and the current Beijing-date Daily Profile.
- They do not alter global Codex configuration, global agents, Hooks, environment variables, or the frozen v3.2.1 installation.
- Installer lifecycle writes are validated only in explicit fake homes. A separately approved global migration plan and clean global validation remain required pre-stable-release gates.

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

## Result rule

Native Runtime Tests 1-5 now provide the generic runtime evidence for `v4.0.0-rc1`. They replace the earlier prototype's runtime-validation-needed status. This is a release-candidate validation record, not a stable `v4.0.0` declaration.
