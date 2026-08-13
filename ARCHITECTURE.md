# v4.1.0-rc3 Native Architecture Note

Status: `v4.1.0-rc3 — PUBLISHED PRERELEASE / RECORDED RUNTIME ACCEPTANCE PASS`

`v4.0.0` remains the stable release. The published RC1 retains its recorded real global upgrade and fresh-session Global Runtime G1-G7 PASS, and the published RC2 recorded `FRESH_REPO_CONTEXT_DELEGATION_PASS`. The published RC3 prerelease passed its recorded real RC1→RC3 Global upgrade and fresh-session Sol-only and delegated Receipt acceptance. RC3 changes only the installer-managed Global `AGENTS.md` policy payload, manifest version and ownership metadata, tests, and documentation. Selector, agents, configuration, state, ModelDial, and migration semantics are unchanged.

## Flow

```text
GPT-5.6 Sol
  -> Global / Project AGENTS delegation policy
  -> Daily Selector
  -> Native custom Luna agent (native agent_type)
  -> GPT-5.6 Luna / selected effort
  -> Native leaf ([agents] enabled = false)
  -> Sol Acceptance Gate
  -> Delegation Receipt
```

## ModelDial source flow

```text
Valid same-day Daily Profile -> reuse immediately
Otherwise:
  Official ModelDial API v1
    -> invalid or unavailable: Official Full Snapshot JSON
    -> invalid or unavailable: valid LKG
    -> invalid or unavailable: NO_LUNA_PROFILE_AVAILABLE
```

The API adapter accepts only schema `1.0` from the published [OpenAPI 3.1 contract](https://modeldial.com/openapi-v1.json), first-party provenance, a coherent batch, and exactly one row for each canonical Luna effort through the `codex` / `gpt-5.6-luna` / `official_login` route. A valid API response stops acquisition. Sources are never merged or arbitrated. Radar HTML runtime fallback is removed in v4.1.

## Stable boundary

- Sol is the sole planner, architect, orchestrator, ambiguity resolver, and final reviewer.
- The inherited Global `AGENTS.md` policy invokes the installed selector for the current Beijing-day role before non-trivial delegation. Repository policy does not maintain a second Daily role authority.
- The five stable roles map `low`, `medium`, `high`, `xhigh`, and `max` to native custom agents running GPT-5.6 Luna at the selected effort. `ultra` is excluded.
- Native `agent_type`/custom-agent selection is the only model and effort boundary. There is no direct model override.
- Every formal Luna custom agent has `[agents] enabled = false`; Luna is a native leaf and cannot spawn or delegate.
- At most three native Luna children may run concurrently.
- The selector owns daily role choice. It does not spawn agents or perform acceptance.
- Project development state lives under ignored `.var/` and is non-authoritative for actual Codex project delegation. Global state is explicitly rooted at `<CODEX_HOME>/sol-luna-v4/state` and contains only the daily profile, v4 LKG, and selector lock.
- Global policy is rendered from `templates/AGENTS.global.md` with safely quoted selector and state paths; it does not install the repository policy verbatim.
- After receipt-eligible non-trivial work, the Global policy emits at most one final-line Delegation Receipt from already-observed facts. Delegated receipts contain the actual selected role and direct-child count; `parallel` appears only for verified overlap. Sol-only receipts contain one high-level outcome reason.

## Explicit non-goals

- No Hook Router, Hook Trust layer, managed-child registry, daemon, background scheduler, database, dashboard, IPC server, plugin framework, or custom orchestration engine.
- No unapproved global Codex mutation. Installer writes require an explicit target, and repository-local validation is restricted to `.tmp/installer-validation/`; routine lifecycle tests use fake homes only.
- No Receipt-driven delegation, lower threshold, forced spawn or parallelism, extra selector call, child inspection, file or network read, state, telemetry, or private reasoning exposure. Receipt text is not runtime attestation.
- CI and static checks are supporting evidence; Native Runtime Tests 1-5 are the runtime gate.

## Global migration transaction

- Only an exact legacy manifest version `3.2` is supported; unknown or malformed manifests fail closed.
- Migration backs up every changed, removed, newly created, and commit-marker path. It does not convert legacy state or access the live selector source.
- Five agents, selector, shared config/policy, exact legacy-owned groups, and exact legacy-owned files are applied and validated before commit.
- `<CODEX_HOME>/sol-luna-v4/install-manifest.json` is atomically written last as the v4 commit marker.
- The old manifest is cleaned up after commit. A cleanup-only failure records `LEGACY_MANIFEST_CLEANUP_PENDING` and is retried without rolling back valid v4 content.
- Unowned `sol-luna-router/audit-bundles/` content is `PRESERVE_REVIEW_REQUIRED` and is never part of installer cleanup.

## Runtime status

Native Runtime Tests 1-5 are recorded as generic `PASS` for the stable v4.0.0 release:

1. Project custom-agent discovery passed in a fresh project session.
2. Explicit native spawn passed with the named custom agent's GPT-5.6 Luna model and configured effort.
3. `AGENTS.md` policy delegation passed: Sol used the current Daily Profile selected role and performed acceptance.
4. Native leaf enforcement passed: `[agents] enabled = false` removed child multi-agent/delegation tools.
5. Parallel native delegation passed: two independent bounded checks used the selected role and Sol consolidated the result.

The generic record intentionally contains no session IDs, usernames, absolute paths, rollout IDs, or installation IDs.

The published RC1 passed its recorded real global upgrade and fresh-session Global Runtime G1-G7 for discovery, selector plus explicit Luna, automatic delegation, native leaf, native parallel execution, Sol acceptance, and legacy absence in one Codex Desktop/App Server environment. The published RC2 recorded `FRESH_REPO_CONTEXT_DELEGATION_PASS`. The published RC3 prerelease passed its recorded real RC1→RC3 Global upgrade, installer idempotency and rollback-readiness checks, plus fresh-session Sol-only and delegated Receipt cases with parent-visible child evidence. The delegated case verified three direct `luna_max` children, native leaf behavior, parallel overlap, and Sol acceptance; the Sol-only case verified zero direct children.

## Compatibility boundary

`v4.0.0` is validated against the tested Codex Desktop/App Server environment and makes no compatibility promise for future Codex versions. RC3's recorded runtime results apply to the actual Codex environment in which they were observed; they do not claim real runtime validation for every operating system, client, account, or user. Legacy audit bundles, migration backups, and trusted Hook metadata are non-runtime residual evidence, not current architecture dependencies.

## Official references

- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
