# Codex Sol Brain + Luna Daily Best v4.0.0-rc1 Native

Status: `v4.0.0-rc1 — NATIVE RUNTIME PASS`

This release candidate uses Codex's native custom-agent runtime. The user selects `gpt-5.6-sol` for the primary session. Sol owns planning, architecture, orchestration, ambiguity resolution, and final acceptance. Clear bounded execution work is delegated only through the current Daily Profile's selected native Luna agent.

Native Runtime Tests 1-5 have generic `PASS` results. The evidence record intentionally omits session IDs, usernames, absolute paths, rollout IDs, and installation IDs.

## Architecture

```text
GPT-5.6 Sol
  -> project AGENTS.md delegation policy
  -> Daily Profile selected role
  -> Native custom Luna agent (native agent_type)
  -> GPT-5.6 Luna / selected effort
  -> Native leaf ([agents] enabled = false)
  -> Sol Acceptance Gate
```

Stable mappings are `low -> luna_low`, `medium -> luna_medium`, `high -> luna_high`, `xhigh -> luna_xhigh`, and `max -> luna_max`. Luna never uses `ultra`. The selected custom agent is the only model/effort selection boundary; there is no direct model override.

Sol remains the sole planner, orchestrator, ambiguity resolver, and final reviewer. Every formal Luna custom agent is a native leaf with `[agents] enabled = false`, so the child cannot spawn or delegate to another agent.

## Explicit non-goals

The runtime contains no Hook Router, Hook Trust layer, managed-child registry, daemon, background scheduler, database, dashboard, IPC server, plugin framework, or custom orchestration engine. Native `agent_type`/custom-agent selection and the project `AGENTS.md` policy are the only delegation mechanisms.

## Runtime status

| Native Runtime Test | Result | Scope of the generic evidence |
| --- | --- | --- |
| 1. Project custom-agent discovery | `PASS` | The five project custom agents were discoverable in a fresh project session. |
| 2. Explicit native spawn | `PASS` | A named custom agent ran as GPT-5.6 Luna at its configured effort and returned the required sentinel. |
| 3. `AGENTS.md` policy delegation | `PASS` | Sol read the current Daily Profile, delegated to its selected role, and performed acceptance. |
| 4. Native leaf | `PASS` | `[agents] enabled = false` prevented child multi-agent/delegation tools. |
| 5. Parallel native delegation | `PASS` | Two independent bounded checks used the selected role and Sol consolidated the result. |

The tests validate the native runtime architecture for this release candidate. They do not grant Luna planning, architecture, orchestration, or final-acceptance authority.

## Why v4

The mandatory Hook-enforcement route is a historical v3 prototype path. It was not reliable for real collaboration spawns in the observed Codex Desktop V2 runtime, so this release candidate uses native project custom agents plus the `AGENTS.md` delegation policy. There is no Hook-based dependency in the current architecture.

## Selector

The fixtures-first selector requires all five canonical Luna rows, chooses the highest score, resolves ties toward lower effort, degrades to the best locally supported effort, locks once per Beijing calendar day, uses an LKG for invalid live snapshots, and fails closed on first-install source failure.

The live adapter is opt-in. It prefers a complete first-party JSON publication and falls back to a complete five-effort batch extracted from the first-party Radar HTML under the same HTTPS allowlist. CI never accesses ModelDial.

```powershell
python src/selector.py --snapshot fixtures/modeldial/complete.json
python src/selector.py --live
python -m unittest discover -s tests -v
```

First-party discovery: [ModelDial Radar](https://modeldial.com/zh-CN/radar) and its [published snapshot JSON](https://modeldial.com/data/reference-snapshots/latest.json) .

## Installer validation

```powershell
python scripts/probe_capabilities.py
python scripts/install.py --dry-run
python scripts/install.py --apply --codex-home .tmp/installer-validation/manual/.codex --validation-sandbox
```

Dry-run remains the default. Mutating installer modes require an explicit `--codex-home`; targets inside the repository additionally require `--validation-sandbox` and must stay below `.tmp/installer-validation/`. Clean install, merge, idempotency, upgrade, manifest-owned legacy migration, backup, exact rollback, and uninstall are validated only against isolated fake homes. No global installation is performed or authorized by this release candidate.

## Release boundary

`v4.0.0-rc1` is a release candidate, not stable `v4.0.0`. Before a stable release, an explicitly approved global migration plan and clean global validation must still be completed. Sandbox installer validation does not authorize writes to a user's real Codex home.

See [RUNTIME_TESTS.md](RUNTIME_TESTS.md) and [ARCHITECTURE.md](ARCHITECTURE.md) for the evidence-calibrated runtime and architecture records.
