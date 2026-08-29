# v4.1.4 Stable Architecture Note

`v4.1.4` is the current Stable release and default installation target.
Stable runtime Source Commit A is
`6a537b445ad6f17a9600c05e655f51a2844bfcc8`; exact-SHA source CI run
`33264634602` passed on Windows, Ubuntu, and macOS with `366` tests all
`PASS`. The reviewed Stable Setup contract is pinned at immutable documentation
Commit `bf01c438eae66f5ef9a27d401c6ee845f89d5d59`, and the current public
Assisted Installation contract is pinned at immutable documentation Commit
`7494d47574ac751e76a231033a0ed91686899a07`; both current documentation anchors
are distinct from the runtime source. The immutable `v4.1.4` tag retains the
originally published Assisted anchor
`5e1ce80d3ed444834f700ac0154bfe444dec8cd3`; the newer anchor corrects only its
release-lineage wording and changes no Setup, source, tag, or Release identity.
`v4.1.3` remains the previous immutable Stable release, with historical runtime
Source Commit `71894e2ef5007c9ba3e6f9d9efbf91cbdad302b4`, Setup anchor
`5c29abc9aed340f4a7c45c22a0f8b36242b920bb`, and Assisted Installation anchor
`23eeba1a5fb21e0483f4140aeca18b483f3e85bf`. `v4.1.2` is an older Stable, with
historical runtime
Source Commit `551520c2435aca94d60132f292edbd53cc975cbe`, Setup anchor
`4b2a6004fb92b6661166cb73e656cc2888b0a2ef`, and Assisted Installation anchor
`a130c676fa5924e44034dc8c27f3dc0abfc3bcad`. `v4.1.1` is an older Stable, with
historical runtime
Source Commit `ca8e9e4caf5564ffe8d0a11fe376047594f8a748`, Setup anchor
`d4a044a04df509285ef38c6afc28b5a68a48a0f9`, and Assisted Installation anchor
`17eb1d370929e884f91c5f1920a2e0868ce4a421`. `v4.1.0-rc6` remains an
immutable historical Prerelease / Preview / Public Beta, and `v4.1.0-rc5` is
an older historical Preview.

Status: `v4.1.4 — CURRENT STABLE RELEASE / DEFAULT INSTALLATION TARGET`; `v4.1.3 — PREVIOUS IMMUTABLE STABLE`

The documented-environment RC5 O1-O10 record remains bounded historical evidence; its Final O4/O9 re-certification was not obtained due to `CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`, with no confirmed product-runtime regression. RC6 independently passed its recorded real Global upgrade, fresh-task O1-O10 acceptance, Final O4/O9 re-certification, and Runtime Cases A/B/C/D in one native Windows Codex environment before the Stable transition. The v4.1.2 transaction then upgraded that baseline while preserving the accepted selector, policy, agent, and configuration content outside the declared installer-owned changes. After explicit Daily selection initialization, an independent one-run fresh-task compatibility smoke passed all seven recorded checks and final Compatibility against the observed installed product runtime. This evidence remains environment- and scenario-bounded. RC4 remains historical release evidence for Receipt reason evidence-gating.

## v4.1.4 Stable boundary

The release closes the uninstall transaction-safety gap found by the final
v4.1.3 audit. Uninstall now verifies its centralized backup before modifying
any managed path and routes every later exception through exact rollback before
preserving the original stable installer error. Regression tests prove that a
backup verification failure leaves the exact installed tree unchanged and that
an exception after one effective uninstall operation restores the exact
pre-uninstall tree.

The installer and ModelDial User-Agent advance to `v4.1.4`; manifest schema
remains `1`. A valid v4.1.3-to-v4.1.4 fake-home upgrade changes only the
installed selector and ownership manifest, creates and verifies one normal
transaction backup, is idempotent on second apply, rolls back exactly, and
fails closed without writes when the previously owned selector was modified.

Stable Source Commit A
`6a537b445ad6f17a9600c05e655f51a2844bfcc8` passed exact-SHA CI run
`33264634602` on Windows, Ubuntu, and macOS with `366` tests all `PASS`.
Repository and fake-home evidence are not real installed-runtime evidence: no
real Global v4.1.4 apply, authentication test, Daily state write, or fresh-task
compatibility smoke is claimed. Stable publication is represented by the
annotated `v4.1.4` tag and a non-draft, non-prerelease GitHub Release; the
public README pins the immutable Setup and Assisted Installation anchors shown
above.

## v4.1.3 Stable boundary

`v4.1.3` is the previous immutable Stable release.

The release is a selector compatibility and provenance maintenance release. It
accepts ModelDial API schemas `1.0` and `1.1` while deliberately retaining the
v4.1 backend-score contract. For schema `1.1`, only the backward-compatible
`rankings` backend axis is eligible; canonical rows must declare
`scoreBasis = backend`, and `score` must equal `backendScore`. The selector does
not consume `overallRankings`, `overallBatch`, capability publications,
`changes.json`, or advisory Agent Profiles.

The official Full Snapshot fallback uses the same `codex` / `official_login`
route identity for score selection and optional reference-cost comparison. It
reads provider and route identity from `model_configuration.provider_id` and
`model_configuration.route_type`, requires first-party-controlled score and
route provenance, and keeps reference-cost validation fail-soft and
selection-neutral.

The source order remains API v1 -> Full Snapshot -> valid LKG -> fail closed.
Daily Profile metadata schema `1`, the normalized LKG envelope, five-effort
winner and lower-effort tie-break semantics, native agents, policy, config,
concurrency, and installer manifest schema `1` remain unchanged. A valid
v4.1.2-to-v4.1.3 upgrade is expected to change only the installed selector and
ownership manifest. Stable Source Commit A
`71894e2ef5007c9ba3e6f9d9efbf91cbdad302b4` passed exact-SHA CI run
`33253340074` on Windows, Ubuntu, and macOS with `363` tests all `PASS`;
evidence commit `bafc41b50269a0b65aba64594e850f6171a714ac` passed CI run
`33253429974` on the same platforms. Repository fake-home lifecycle and
read-only live-source checks are recorded separately from real runtime. No real
Global v4.1.3 apply or candidate fresh-task smoke is claimed. The immutable
Setup and Assisted Installation anchors are recorded above. Stable publication
is represented by the annotated `v4.1.3` tag and a non-draft,
non-prerelease GitHub Release; that release's historical README used the same
immutable chain.

## v4.1.2 Stable boundary

`v4.1.2` is an older published immutable Stable release.
Source Commit A is `551520c2435aca94d60132f292edbd53cc975cbe`. Exact-SHA CI run
`32717295801` passed on Windows, Ubuntu, and macOS and reported `357` tests all
`PASS`. Current-master evidence commit
`fac118ac5ca096aaf1ef8d68b79bfc1372998a5a` also passed its three-platform
source CI run `32717520585`; it is evidence for the current tip, not an
alternate Source Commit A or installer identity. The public GitHub Release is
non-draft and non-prerelease.

The recorded transaction started from the real Global `v4.1.0-rc6` baseline with
source `50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49`. A detached exact-Source-A
dry-run returned `DRY_RUN_PASS`, `writes NO`, `effective_changes 2`, and
five-effort capability `PASS`. Apply returned `UPGRADED`,
`configuration_preserved true`, and `effective_changes 2`; only the selector
and `install-manifest` changed, and one transaction backup was created. A
second apply returned `CURRENT_INSTALLATION_PASS`, `writes NO`,
`effective_changes 0`, and `backup NONE`.

The Daily proof returned a legal role and matching effort without recording the
day-specific effort; same-day Profile and LKG were not rewritten. Exactly one
fresh-task compatibility smoke ran for about `169.4` seconds with
`codex-cli 0.146.0`, exited `0`, and passed `CLI`, `Luna capability`,
`Selector`, `Delegation`, `Protected state`, `Runtime contract`, and final
`Compatibility`. Pre/post hashes for `AGENTS.md`, configuration, all five
agents, selector, manifest, Profile, LKG, and lock were unchanged, and the
smoke created no backup.

This is evidence from one native Windows Codex environment. Windows, Ubuntu,
and macOS CI are source validation only, not three-platform real-runtime
validation. The Stable change tightens the child-process environment boundary
to purpose-specific allowlists; it does not change the Sol/Luna architecture,
five-effort model, native-leaf rule, or acceptance ownership.

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

The API adapter accepts schemas `1.0` and `1.1` from the published [OpenAPI 3.1 contract](https://modeldial.com/openapi-v1.json), first-party provenance, a coherent backend batch, and exactly one row for each canonical Luna effort through the `codex` / `gpt-5.6-luna` / `official_login` route. Schema `1.1` must preserve backend score identity as defined above. A valid API response stops acquisition. Sources are never merged or arbitrated. Radar HTML runtime fallback is removed in v4.1.

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

## RC6 release delta

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

## Historical v4.1.0 Stable release delta

- The installer payload moves from `v4.1.0-rc6` to `v4.1.0` with manifest
  schema `1` unchanged.
- An RC6 -> Stable fake-home upgrade changes only
  `sol-luna-v4/install-manifest.json`; the selector, Global policy, five Luna
  agents, config, Daily Profile, and LKG remain byte-identical.
- Dry-run zero-write behavior, transaction backup, second-apply idempotency,
  exact rollback, downgrade refusal, and ownership-conflict fail-closed
  behavior are covered by repository lifecycle tests.

## v4.1.1 Stable installation assistance

The Stable installation assistant adds an orchestration layer around the existing
installer without changing installed selector, policy, agent, or config
payloads:

```text
conversation bootstrap for missing Python/Git
  -> read-only check and aggregate blockers
  -> exact recovery plan + SHA-256 Plan ID
  -> explicit approval for catalogued system commands
  -> clean detached exact-source verification
  -> five ephemeral read-only Luna capability calls
  -> installer dry-run
  -> optional explicitly authorized installer apply
  -> reload when required
  -> explicit Daily selector initialization and proof
  -> separate fresh-task compatibility smoke
```

`scripts/install_assist.py` owns orchestration state only in memory and JSON
output. It creates no preflight state file and never edits managed runtime
content. `scripts/install_recovery_catalog.json` is data, not a shell program;
validated argument vectors are the only executable recovery form. The existing
`scripts/install.py` remains the only authority for ownership, target writes,
transaction backup, rollback, migration, and uninstall.

The selector initialization handoff runs the installed selector with
`--ensure-daily --print-selection` only after any required reload. It is an
explicit normal selector-state operation and must prove an allowed role plus
its matching effort before the flow opens a separate fresh task. The
compatibility smoke remains read-only and status-only; it never initializes
Daily selection or retries a failed initialization.

The Stable source bumps only installer manifest version from `v4.1.0` to
`v4.1.1`; the installed payload remains byte-identical. A valid `v4.1.0` to
`v4.1.1` fake-home upgrade therefore changes only
`sol-luna-v4/install-manifest.json`. Source Commit A2 passed 332 local tests and
exact-SHA CI on Windows, Ubuntu, and macOS. After explicit Daily selection
initialization, the independent fresh-task compatibility smoke ran once for
about 144.2 seconds and passed `CLI`, `Luna capability`, `Selector`,
`Delegation`, `Protected state`, `Runtime contract`, and final `Compatibility`.
No real Global `v4.1.1` installer apply was performed.

## Explicit non-goals

- No Hook Router, Hook Trust layer, managed-child registry, daemon, background scheduler, database, dashboard, IPC server, plugin framework, or custom orchestration engine.
- No unapproved global Codex mutation. Installer writes require an explicit target, and repository-local validation is restricted to `.tmp/installer-validation/`; routine lifecycle tests use fake homes only.
- No Receipt-driven delegation, lower threshold, forced spawn or parallelism, extra selector call, capability probe, child inspection, tool, file or network read, network access, state, telemetry, repository write, or private reasoning exposure. Receipt text is not runtime attestation.
- CI and static checks are supporting evidence; Native Runtime Tests 1-5 are the runtime gate.

## Stable runtime evidence boundary

`v4.1.1` preserves the RC6 selector behavior, including malformed URL parsing,
hostname, and port `ValueError` normalization. The installer payload version
moves from `v4.1.0` to `v4.1.1`, but a `v4.1.0`→`v4.1.1` apply changes only the
ownership manifest. The installation assistant, compatibility smoke, and
acceptance harness are tooling only and do not modify product runtime by
themselves.
`CODEX_SOL_LUNA_SETUP.md`, `RUNTIME_TESTS.md`, this architecture note, and
`SECURITY.md` form the acceptance contract and may be updated as that boundary
evolves. `V410_TO_V411_INSTALLED_BEHAVIOR_CHANGED = NO`;
`ACCEPTANCE_CONTRACT_CHANGED = YES`.

The historical RC6 acceptance harness builds RC6 Source Commit A under a unique owned
acceptance root. O4 and O9 run with an isolated `CODEX_HOME`, home/profile,
application-data, temporary-storage, and XDG environment. One
`isolated_runtime_env` is explicitly propagated to every harness subprocess;
the O9 in-process fail-soft and status/health path runs under the same mapping
and restores the caller environment afterward. Before the first installer
write or credential copy, the harness validates the temporary parent
and planned isolated home. Symlinks, junctions, reparse points, mount points,
path overlap, shared identity, and hardlinks across the isolated/real boundary
fail closed; the fixed macOS `/var` system alias is the only platform-root
exception. RC6 real Global upgrade, O1-O10 acceptance, and Final O4/O9
re-certification are recorded `PASS` in the documented environment. The real
Global target was used only for installed-state and protected-state integrity
checks during acceptance; isolated or controlled state was used where a case
required missing, degraded, capability-limited, invalid, or unavailable input.

The real `CODEX_HOME` is not a runtime-attribution source. Its role is limited
to pre/post `PROTECTED_SOL_LUNA_STATE` integrity and root-identity verification.
Managed Sol/Luna policy, configuration, agents, selector, manifest, Daily
Profile, LKG, `selector.lock`, and every other entry in
`sol-luna-v4/state/**` must remain unchanged. The tree comparison includes
hash, type, device/file identity, link count, and reparse status; unrelated
real-home runtime activity is ignored by the historical RC6 case decision.

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

Native Runtime Tests 1-5 are recorded as generic `PASS` for the v4 native architecture:

1. Project custom-agent discovery passed in a fresh project session.
2. Explicit native spawn passed with the named custom agent's GPT-5.6 Luna model and configured effort.
3. `AGENTS.md` policy delegation passed: Sol used the current Daily Profile selected role and performed acceptance.
4. Native leaf enforcement passed: `[agents] enabled = false` removed child multi-agent/delegation tools.
5. Parallel native delegation passed: two independent bounded checks used the selected role and Sol consolidated the result.

The generic record intentionally contains no session IDs, usernames, absolute paths, rollout IDs, or installation IDs.

The documented-environment RC5 O1-O10 record, including O4 and O9, remains
bounded historical evidence. RC5 Final O4/O9 re-certification was not obtained
due to `CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`; no confirmed product-runtime
regression is reported. RC6 independently passed the repeatable isolated
O2/O4/O9 harness, including the pre-write, cleanup, redirection, hardlink, and
runtime-category boundaries described above. RC6 also passed its separately
recorded real Global upgrade, O1-O10 matrix, Final O4/O9 re-certification, and
fresh-session Runtime Cases A/B/C/D. The real protected Sol/Luna state and root
identity were unchanged, observed unknown paths were zero, and acceptance
residuals were zero. This is not a claim of real-runtime validation across all
CI platforms, clients, accounts, or users.

Stable Source Commit A2 passed repository validation and exact-SHA CI on
Windows, Ubuntu, and macOS. Its `v4.1.0`→`v4.1.1` lifecycle coverage proves that
the installed behavior is unchanged apart from manifest version/source
metadata. After explicit Daily selection initialization, the independent
fresh-task compatibility smoke ran once for about 144.2 seconds and passed CLI,
Luna capability, Selector, Delegation, Protected state, Runtime contract, and
final Compatibility checks. It did not perform a real Global `v4.1.1` apply
and does not widen the historical RC6 runtime-evidence boundary.

The published RC1 passed its recorded real global upgrade and fresh-session Global Runtime G1-G7 for discovery, selector plus explicit Luna, automatic delegation, native leaf, native parallel execution, Sol acceptance, and legacy absence in one Codex Desktop/App Server environment. The published RC2 recorded `FRESH_REPO_CONTEXT_DELEGATION_PASS`. The published RC3 prerelease passed its recorded real RC1→RC3 Global upgrade, installer idempotency and rollback-readiness checks, plus fresh-session Sol-only and delegated Receipt cases with parent-visible child evidence. The published RC4 prerelease passed its recorded real RC3→RC4 Global upgrade and Runtime Cases A/B/C/D: reasoning-only, three-child delegated parallel execution, the no-independent-work regression, and the controlled genuine-unavailability evidence gate. RC4 changed only Receipt reason evidence-gating; the architecture flow and authority boundaries above remain unchanged.

## Compatibility boundary

`v4.1.1` is validated only against the documented Codex environments and makes no compatibility promise for future Codex versions. RC3, RC4, and RC6 recorded runtime results apply only to the actual Codex environments in which they were observed. No record claims real runtime validation for every operating system, client, account, or user. Three-platform CI is source validation, not three-platform real Codex runtime validation. Legacy audit bundles, migration backups, and trusted Hook metadata are non-runtime residual evidence, not current architecture dependencies.

## Official references

- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
