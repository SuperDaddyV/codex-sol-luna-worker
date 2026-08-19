# v4.1.0-rc5 Source Candidate Architecture Note

`v4.1.0-rc5 — Observability & UX` is a source candidate, not a published
release. `v4.1.0-rc4` remains the published Preview prerelease and `v4.0.0`
remains Stable. RC5 Source Commit A is
`5ae88ff9190b31174c55a6136c0c8c8611d0b34c`; the immutable setup contract is
available at documentation commit
`7affbcda6f68cd125aaf6eec3c0e3ff04ebd60d9`.

Status: `v4.1.0-rc4 — PUBLISHED PRERELEASE / CURRENT PREVIEW / RUNTIME ACCEPTANCE PASS`

`v4.0.0` remains the stable release, and `v4.1.0-rc4` is the current published preview prerelease. RC4 fixes only Receipt reason evidence-gating: without current-task parent-visible availability failure evidence, a Sol-only Receipt cannot report `Luna unavailable`. RC4 changes only the installer-managed Global `AGENTS.md` policy payload, manifest version and ownership metadata, tests, and documentation. Selector, agents, configuration, state, ModelDial, delegation threshold, concurrency, native leaf behavior, Task Contract, Context Firewall, Daily authority, Sol Acceptance, installer, and migration semantics are unchanged.

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
- After receipt-eligible non-trivial work, the Global policy emits at most one final-line Delegation Receipt from already-observed facts. Delegated receipts contain the actual selected role and direct-child count; `parallel` appears only for verified overlap. Sol-only receipts contain one high-level outcome reason. `Luna unavailable` is evidence-gated: the current task's normal delegation path must already have produced parent-visible selector or native-agent availability failure evidence. No selector invocation, no child attempt, Sol retention, docs-only work, or sequential/tightly coupled execution does not establish unavailability, and `Luna unavailable` is never the default fallback.

## RC5 observability flow

- The selector normalizes score provenance once and optionally projects only validated same-batch, same-pricing, same-effort ModelDial reference-cost pairs. Invalid cost metadata is fail-soft and cannot invalidate otherwise valid Luna scores or change winner and tie-break semantics.
- A new Daily Profile records metadata schema `1` and projects only the actual selected effort. Existing same-day RC4 profiles are reused byte-for-byte without refresh, backfill, migration, network access, or state writes. New LKG records keep the existing `{"snapshot": ...}` envelope around the canonical normalized snapshot; legacy LKG remains valid.
- `--print-selection` is the structured selection metadata boundary for delegation and Receipt rendering. The saved result supplies role, effort, fallback, capability degradation, source winner, and an optional reference-cost comparison. `--print-role` remains stdout- and exit-compatible with RC4.
- `--status-json` enters one read-only health reader before fetch, snapshot loading, Daily selection, and the selector lock. Status and diagnostic UX share this reader; it performs zero network access, selector locks, state writes, state-directory creation, and Luna spawn or availability probes.
- Health priority is `Misconfigured > Unavailable > Degraded > Healthy`. Absence of today's profile is Healthy with selection not initialized; status cannot manufacture unavailable evidence.
- The diagnostic report is constructed from an exact whitelist and then sanitized. It exposes symbolic locations rather than real private paths and contains no environment dump, configuration or policy content, arbitrary URL, log, credential, exception message, or child reasoning.
- The installed state directory remains the single state authority. RC5 adds no dashboard, daemon, telemetry, background service, router, sidecar state, or database.

## Explicit non-goals

- No Hook Router, Hook Trust layer, managed-child registry, daemon, background scheduler, database, dashboard, IPC server, plugin framework, or custom orchestration engine.
- No unapproved global Codex mutation. Installer writes require an explicit target, and repository-local validation is restricted to `.tmp/installer-validation/`; routine lifecycle tests use fake homes only.
- No Receipt-driven delegation, lower threshold, forced spawn or parallelism, extra selector call, capability probe, child inspection, tool, file or network read, network access, state, telemetry, repository write, or private reasoning exposure. Receipt text is not runtime attestation.
- CI and static checks are supporting evidence; Native Runtime Tests 1-5 are the runtime gate.

## RC5 runtime acceptance isolation boundary

The RC5 acceptance harness builds Source Commit A in a fresh fake `CODEX_HOME`
and keeps product-runtime validation separate from the real installed-state
audit. It validates the temporary parent and planned fake home before the first
installer write or credential copy. Symlinks, junctions, reparse points, mount
points, path overlap, and hardlinks across the fake/real boundary fail closed.

The real `CODEX_HOME` inventory has three non-overlapping path categories:

- `PROTECTED_SOL_LUNA_STATE` is the managed Sol/Luna policy, configuration,
  agents, selector, manifest, selector state, and backup boundary. Its recorded
  entries must remain unchanged.
- `CODEX_PLATFORM_RUNTIME_STATE` is the explicit authentication and Codex
  session/runtime boundary. Valid activity is reported separately from product
  configuration changes.
- `CODEX_LOCAL_STORAGE_STATE` is the explicit local storage, SQLite,
  computer-use configuration, and memory-content boundary. Valid activity is
  likewise reported without treating it as a Sol/Luna mutation.

Anything outside those categories is an unexpected write. Every recorded path
must remain inside the real runtime root, use a supported file or directory
type, avoid reparse redirection, and have no unexpected hardlinks. Temporary
cleanup is limited to a direct child with the harness prefix, the original
directory identity, and a matching per-run ownership marker and token. Reparse
entries are removed as entries and are never traversed.

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

The separately authorized RC5 source-candidate runtime acceptance recorded
O1-O10 as `PASS` and status `RC5_RUNTIME_CATEGORY_MODEL_FIXED` in one observed
Codex environment. The repeatable harness adds isolated O2, O4, and O9 coverage
plus the pre-write, cleanup, redirection, hardlink, and runtime-category
regressions described above. This bounded evidence does not publish RC5, change
the Stable architecture, or claim real-runtime validation across all CI
platforms, clients, accounts, or users.

The published RC1 passed its recorded real global upgrade and fresh-session Global Runtime G1-G7 for discovery, selector plus explicit Luna, automatic delegation, native leaf, native parallel execution, Sol acceptance, and legacy absence in one Codex Desktop/App Server environment. The published RC2 recorded `FRESH_REPO_CONTEXT_DELEGATION_PASS`. The published RC3 prerelease passed its recorded real RC1→RC3 Global upgrade, installer idempotency and rollback-readiness checks, plus fresh-session Sol-only and delegated Receipt cases with parent-visible child evidence. The published RC4 prerelease passed its recorded real RC3→RC4 Global upgrade and Runtime Cases A/B/C/D: reasoning-only, three-child delegated parallel execution, the no-independent-work regression, and the controlled genuine-unavailability evidence gate. RC4 changed only Receipt reason evidence-gating; the architecture flow and authority boundaries above remain unchanged.

## Compatibility boundary

`v4.0.0` is validated against the tested Codex Desktop/App Server environment and makes no compatibility promise for future Codex versions. RC3 and RC4 recorded runtime results apply only to the actual Codex environments in which they were observed. Neither record claims real runtime validation for every operating system, client, account, or user. Three-platform CI is source validation, not three-platform real Codex runtime validation. Legacy audit bundles, migration backups, and trusted Hook metadata are non-runtime residual evidence, not current architecture dependencies.

## Official references

- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
