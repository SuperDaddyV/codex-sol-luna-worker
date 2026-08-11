# v4.0.0-rc1 Native Architecture Note

Status: `v4.0.0-rc1 — NATIVE RUNTIME PASS`

## Flow

```text
GPT-5.6 Sol
  -> project AGENTS.md delegation policy
  -> Daily Profile selected role
  -> Native custom Luna agent (native agent_type)
  -> GPT-5.6 Luna / selected effort
  -> Native leaf ([agents] enabled = false)
  -> Sol Acceptance Gate
```

## Stable boundary

- Sol is the sole planner, architect, orchestrator, ambiguity resolver, and final reviewer.
- `AGENTS.md` is the delegation policy. It requires the current Beijing-date Daily Profile and its `selected_role` before non-trivial delegation.
- The five stable roles map `low`, `medium`, `high`, `xhigh`, and `max` to native custom agents running GPT-5.6 Luna at the selected effort. `ultra` is excluded.
- Native `agent_type`/custom-agent selection is the only model and effort boundary. There is no direct model override.
- Every formal Luna custom agent has `[agents] enabled = false`; Luna is a native leaf and cannot spawn or delegate.
- The selector owns daily role choice and repo-local state. It does not spawn agents or perform acceptance.
- Runtime state lives under `.var/` and is never committed.

## Explicit non-goals

- No Hook Router, Hook Trust layer, managed-child registry, daemon, background scheduler, database, dashboard, IPC server, plugin framework, or custom orchestration engine.
- No unapproved global Codex mutation. Installer writes require an explicit target, and repository-local validation is restricted to `.tmp/installer-validation/`; RC1 lifecycle tests use fake homes only.
- CI and static checks are supporting evidence; Native Runtime Tests 1-5 are the runtime gate.

## Runtime status

Native Runtime Tests 1-5 are recorded as generic `PASS` for this release candidate:

1. Project custom-agent discovery passed in a fresh project session.
2. Explicit native spawn passed with the named custom agent's GPT-5.6 Luna model and configured effort.
3. `AGENTS.md` policy delegation passed: Sol used the current Daily Profile selected role and performed acceptance.
4. Native leaf enforcement passed: `[agents] enabled = false` removed child multi-agent/delegation tools.
5. Parallel native delegation passed: two independent bounded checks used the selected role and Sol consolidated the result.

The generic record intentionally contains no session IDs, usernames, absolute paths, rollout IDs, or installation IDs.

## Release boundary

`v4.0.0-rc1` is not stable `v4.0.0`. An explicitly approved global migration plan and clean global validation remain required before a stable release. Sandbox lifecycle validation is a separate gate and does not change global Codex state.

## Official references

- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
