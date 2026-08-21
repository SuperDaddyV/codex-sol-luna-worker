# v4.1.0-rc6 Source Candidate Architecture Note

`v4.1.0-rc6` is a master-tree source candidate, not tagged, published, Stable,
or the default installation target. RC6 Source Commit A is
`50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49`; exact-SHA CI passed on Windows,
Ubuntu, and macOS. Its immutable candidate setup contract is documentation
Commit `86424ea4d6f6630a34b6e4daa22d2d93a5576ddf`; that contract is not the
default entry or runtime source. The published/default Preview remains `v4.1.0-rc5` through
immutable setup anchor `ccd9d84da2f74df9ca2d919729b75eebf2dac27a`, and
`v4.0.0` remains Stable.

Status: `v4.1.0-rc5 — PUBLISHED PRERELEASE / CURRENT PREVIEW / DEFAULT INSTALLATION TARGET`

`v4.0.0` remains the Stable release, and `v4.1.0-rc5` is the current published Preview / Public Beta and default installation target. The documented-environment RC5 O1-O10 record remains bounded evidence; Final O4/O9 re-certification was not obtained due to `CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`; no confirmed product-runtime regression is reported. RC6 real Global upgrade and O1-O10 acceptance were not run and do not constitute a final PASS or release claim. RC4 remains historical release evidence for Receipt reason evidence-gating.

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

## RC6 candidate delta

- The selector normalizes malformed URL parsing, hostname, and port `ValueError`
  cases to `SnapshotInvalid`, preserving the API -> snapshot -> LKG ->
  fail-closed source order.
- The installer payload moves to `v4.1.0-rc6` with manifest schema `1`. An
  RC5 -> RC6 fake-home upgrade is expected to change only
  `sol-luna-v4/selector.py` and `sol-luna-v4/install-manifest.json`; idempotency,
  backup, exact rollback, and ownership fail-closed behavior are covered by
  local tests.
- The compatibility-smoke baseline adds dual exact rollout roots and bounded
  writer-settle/fail-closed evidence. The harness is tooling only and does not
  modify product runtime.

## Explicit non-goals

- No Hook Router, Hook Trust layer, managed-child registry, daemon, background scheduler, database, dashboard, IPC server, plugin framework, or custom orchestration engine.
- No unapproved global Codex mutation. Installer writes require an explicit target, and repository-local validation is restricted to `.tmp/installer-validation/`; routine lifecycle tests use fake homes only.
- No Receipt-driven delegation, lower threshold, forced spawn or parallelism, extra selector call, capability probe, child inspection, tool, file or network read, network access, state, telemetry, repository write, or private reasoning exposure. Receipt text is not runtime attestation.
- CI and static checks are supporting evidence; Native Runtime Tests 1-5 are the runtime gate.

## RC6 candidate runtime acceptance isolation boundary

RC6 changes product runtime behavior only in `src/selector.py` for malformed
URL parsing, hostname, and port `ValueError` normalization. The installer
payload version also moves to `v4.1.0-rc6`. The compatibility smoke and
acceptance harness are tooling only and do not modify product runtime.
`CODEX_SOL_LUNA_SETUP.md`, `RUNTIME_TESTS.md`, this architecture note, and
`SECURITY.md` form the acceptance contract and may be updated as that boundary
evolves. `PRODUCT_RUNTIME_CHANGED = YES`;
`ACCEPTANCE_CONTRACT_CHANGED = YES`.

The RC6 acceptance harness builds Source Commit A under a unique owned
acceptance root. O4 and O9 run with an isolated `CODEX_HOME`, home/profile,
application-data, temporary-storage, and XDG environment. One
`isolated_runtime_env` is explicitly propagated to every harness subprocess;
the O9 in-process fail-soft and status/health path runs under the same mapping
and restores the caller environment afterward. Before the first installer
write or credential copy, the harness validates the temporary parent
and planned isolated home. Symlinks, junctions, reparse points, mount points,
path overlap, shared identity, and hardlinks across the isolated/real boundary
fail closed; the fixed macOS `/var` system alias is the only platform-root
exception. RC6 real Global upgrade and O1-O10 acceptance remain unexecuted.

The real `CODEX_HOME` is not a runtime-attribution source. Its role is limited
to pre/post `PROTECTED_SOL_LUNA_STATE` integrity and root-identity verification.
Managed Sol/Luna policy, configuration, agents, selector, manifest, Daily
Profile, LKG, `selector.lock`, and every other entry in
`sol-luna-v4/state/**` must remain unchanged. The tree comparison includes
hash, type, device/file identity, link count, and reparse status; unrelated
real-home runtime activity is ignored by the RC6 case decision.

Runtime attribution is performed inside the isolated home. The
`CODEX_PLATFORM_RUNTIME_STATE` namespace retains the previously enumerated
session, session-index, app-cache, and active-exec paths and adds only
`browser/sessions/**`, `cache/remote_plugin_catalog/**`, `plugins/cache/**`,
`tmp/arg0/**`, and a validated `visualizations/` runtime subtree. It does not
allow their broader parent trees. Root SQLite storage accepts only the
`goals`, `logs`, `memories`, `queue`, `state`, and `thread_history` ID families,
with `-wal` and `-shm` sidecars strongly coupled to a safe base; global
`*.sqlite` and `*.db` matching is forbidden. Anything outside the exact
isolated categories is an unexpected write. Every allowed entry must remain
inside the isolated root, use a supported file or directory type, and have no
unexpected hardlinks. The only runtime reparse exception is an internal
`plugins/cache/**` directory target that passes the shared safe-plugin-cache
contract; external, protected, escaping, and looping targets fail closed.

Temporary cleanup is limited to a direct child with the harness prefix, the
original directory identity, and a matching per-run ownership marker and
token. Reparse entries are removed as entries and are never traversed.

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

The documented-environment RC5 O1-O10 record, including O4 and O9, remains
bounded evidence. Final O4/O9 re-certification was not obtained due to
`CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`; no confirmed product-runtime
regression is reported. The repeatable harness adds isolated O2, O4, and O9
coverage plus the pre-write, cleanup, redirection, hardlink, and
runtime-category regressions described above. RC6 real Global upgrade and
O1-O10 acceptance were not run. None of this is a final PASS or a claim of
real-runtime validation across all CI platforms, clients, accounts, or users.

The published RC1 passed its recorded real global upgrade and fresh-session Global Runtime G1-G7 for discovery, selector plus explicit Luna, automatic delegation, native leaf, native parallel execution, Sol acceptance, and legacy absence in one Codex Desktop/App Server environment. The published RC2 recorded `FRESH_REPO_CONTEXT_DELEGATION_PASS`. The published RC3 prerelease passed its recorded real RC1→RC3 Global upgrade, installer idempotency and rollback-readiness checks, plus fresh-session Sol-only and delegated Receipt cases with parent-visible child evidence. The published RC4 prerelease passed its recorded real RC3→RC4 Global upgrade and Runtime Cases A/B/C/D: reasoning-only, three-child delegated parallel execution, the no-independent-work regression, and the controlled genuine-unavailability evidence gate. RC4 changed only Receipt reason evidence-gating; the architecture flow and authority boundaries above remain unchanged.

## Compatibility boundary

`v4.0.0` is validated against the tested Codex Desktop/App Server environment and makes no compatibility promise for future Codex versions. RC3 and RC4 recorded runtime results apply only to the actual Codex environments in which they were observed. Neither record claims real runtime validation for every operating system, client, account, or user. Three-platform CI is source validation, not three-platform real Codex runtime validation. Legacy audit bundles, migration backups, and trusted Hook metadata are non-runtime residual evidence, not current architecture dependencies.

## Official references

- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
