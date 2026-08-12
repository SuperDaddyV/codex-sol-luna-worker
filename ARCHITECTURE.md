# v4.0.0 Native Architecture Note

Status: `v4.0.0 — STABLE / GLOBAL V4 RUNTIME PASS`

## Flow

```text
GPT-5.6 Sol
  -> Global / Project AGENTS delegation policy
  -> Daily Selector
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
- At most three native Luna children may run concurrently.
- The selector owns daily role choice. It does not spawn agents or perform acceptance.
- Project development state lives under ignored `.var/`. Global state is explicitly rooted at `<CODEX_HOME>/sol-luna-v4/state` and contains only the daily profile, v4 LKG, and selector lock.
- Global policy is rendered from `templates/AGENTS.global.md` with safely quoted selector and state paths; it does not install the repository policy verbatim.

## Explicit non-goals

- No Hook Router, Hook Trust layer, managed-child registry, daemon, background scheduler, database, dashboard, IPC server, plugin framework, or custom orchestration engine.
- No unapproved global Codex mutation. Installer writes require an explicit target, and repository-local validation is restricted to `.tmp/installer-validation/`; routine lifecycle tests use fake homes only.
- CI and static checks are supporting evidence; Native Runtime Tests 1-5 are the runtime gate.

## Global migration transaction

- Only an exact legacy manifest version `3.2` is supported; unknown or malformed manifests fail closed.
- Migration backs up every changed, removed, newly created, and commit-marker path. It does not convert legacy state or access the live selector source.
- Five agents, selector, shared config/policy, exact legacy-owned groups, and exact legacy-owned files are applied and validated before commit.
- `<CODEX_HOME>/sol-luna-v4/install-manifest.json` is atomically written last as the v4 commit marker.
- The old manifest is cleaned up after commit. A cleanup-only failure records `LEGACY_MANIFEST_CLEANUP_PENDING` and is retried without rolling back valid v4 content.
- Unowned `sol-luna-router/audit-bundles/` content is `PRESERVE_REVIEW_REQUIRED` and is never part of installer cleanup.

## Runtime status

Native Runtime Tests 1-5 are recorded as generic `PASS` for this stable release:

1. Project custom-agent discovery passed in a fresh project session.
2. Explicit native spawn passed with the named custom agent's GPT-5.6 Luna model and configured effort.
3. `AGENTS.md` policy delegation passed: Sol used the current Daily Profile selected role and performed acceptance.
4. Native leaf enforcement passed: `[agents] enabled = false` removed child multi-agent/delegation tools.
5. Parallel native delegation passed: two independent bounded checks used the selected role and Sol consolidated the result.

The generic record intentionally contains no session IDs, usernames, absolute paths, rollout IDs, or installation IDs.

Global Runtime G1-G7 also passed for discovery, selector plus explicit Luna, automatic delegation, native leaf, native parallel execution, Sol acceptance, and legacy absence. The Daily Selector passed same-day cache reuse and no-`ultra` runtime checks; its LKG and fail-closed contracts are covered by tests.

## Stable boundary

`v4.0.0` is validated against the tested Codex Desktop/App Server environment and makes no compatibility promise for future Codex versions. Legacy audit bundles, migration backups, and trusted Hook metadata are non-runtime residual evidence, not current architecture dependencies.

## Official references

- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
