# Codex Sol + Luna Worker — v4.1.4 Stable Execution Setup Contract

Contract version: `v4.1.4`.

Release status:

- `v4.1.4` is the Stable release target and default installation target;
- Stable Source Commit A is `6a537b445ad6f17a9600c05e655f51a2844bfcc8`;
- exact-SHA CI run `33264634602` passed on Windows, Ubuntu, and macOS and reported `366` tests all `PASS`;
- no real Global v4.1.4 installer apply or candidate fresh-task runtime smoke was performed;
- `v4.1.3` remains the previous immutable Stable release;
- `v4.1.2`, `v4.1.1`, and `v4.1.0` remain older immutable Stable releases;
- `v4.1.0-rc6` remains an immutable historical Prerelease / Preview / Public Beta;
- `v4.1.0-rc5` is an older historical Preview.

The bilingual README and assisted-installation entry pin this Setup contract
through later exact immutable documentation commits. No document commit is
required to self-reference its own SHA. Stable publication is independently
established by the immutable `v4.1.4` tag and a non-draft, non-prerelease
GitHub Release rather than by this document alone.

Repository fake-home lifecycle validation proves that a clean v4.1.3-to-v4.1.4
upgrade plans and changes only the selector and ownership manifest, creates its
normal transaction backup, is idempotent on second apply, rolls back exactly,
and fails closed without writes when the previously owned selector was modified.
Uninstall validation separately proves that backup verification failure leaves
the installed tree unchanged and that an exception after a partial uninstall
operation restores the exact pre-uninstall tree. Source Commit A passed the
`366`-test three-platform CI gate. Read-only live checks on 2026-08-30
separately proved that both the API
v1.1 path and Full Snapshot fallback selected the backend-axis result and
projected comparable reference-cost metadata. Those observations are
time-bounded source compatibility evidence, not real installed-runtime
acceptance. No real Global v4.1.4 apply, authentication test, Daily state write,
or candidate fresh-task smoke is claimed.

> [!IMPORTANT]
> This is an independent community project. It is not affiliated with, sponsored by, or endorsed by OpenAI or ModelDial. The user must review this contract before execution. `v4.1.4` is the Stable release target and default installation target; `v4.1.3` is the previous immutable Stable, `v4.1.2`, `v4.1.1`, and `v4.1.0` are older Stable releases, and RC6 remains a historical Prerelease. Never silently expand permissions, installation scope, or network access.

This document is the transactional setup contract used by the separately pinned assisted-installation contract. Orchestrate `scripts/install.py`; do not reproduce its merge, ownership, backup, migration, rollback, or uninstall logic with ad hoc shell commands.

Stable runtime Source Commit A:

```text
6a537b445ad6f17a9600c05e655f51a2844bfcc8
```

This setup contract installs the immutable Stable runtime payload from Source
Commit A shown above. The public README pins this contract through the separate
immutable assisted-installation and README documentation commits. A
documentation commit is not the runtime payload source and is never passed to
the installer.

The Stable release advances the installer payload from `v4.1.3` to `v4.1.4`;
manifest schema remains `1`. Repository fake-home validation requires an
upgrade to change only `sol-luna-v4/selector.py` and
`sol-luna-v4/install-manifest.json`, while configuration, policy, five agents,
Profile, LKG, and lock remain protected. The installation assistant,
compatibility smoke, and acceptance harness are repository tooling and do not
modify product runtime by themselves. The acceptance contract consists of this setup contract,
`RUNTIME_TESTS.md`, `ARCHITECTURE.md`, and `SECURITY.md`; those documents may
change when the acceptance design changes.

`V413_TO_V414_INSTALLED_BEHAVIOR_CHANGED = YES`; `ACCEPTANCE_CONTRACT_CHANGED = YES`.

`SETUP_CONTRACT_SELF_REFERENCE_REQUIRED = NO`.

## 0. Document Role

You are the installation agent. Your job is to inspect, plan, back up through the installer, install, validate, and report. Preserve an evidence-based boundary between repository checks and real runtime checks.

You must:

1. obtain the exact approved Stable runtime source commit shown above;
2. discover the current OS, Python, Codex, and target `CODEX_HOME` without guessing;
3. inspect existing state without exposing unrelated private content;
4. run the existing installer dry-run before any mutation;
5. classify the installation mode and stop on uncertainty;
6. use the existing installer transaction for apply, migration, rollback, and uninstall;
7. validate static payloads and then require a fresh Codex task for runtime smoke testing;
8. report what was changed, preserved, backed up, or blocked.

You must not guess paths, overwrite unknown configuration, install system dependencies, change authentication, update Codex, move Git tags, execute mutable `master` content, bypass ownership checks, or silently widen permissions. If a required condition is missing, stop with `BLOCKED` and the exact reason.

## 0A. Installation Preflight

Before cloning or downloading source, creating a temporary source directory, writing capability-probe state, or invoking any installer mode, run a read-only prerequisite preflight. Do not install system dependencies, modify `PATH`, or search internal Codex Desktop application directories for an executable.

This copy-and-paste installation path supports Codex Desktop on Windows, Ubuntu/Linux, or macOS, with WSL treated as a separate Linux environment. It requires all of the following before source acquisition:

- the current Codex Desktop task;
- a `codex` command already resolvable by the task environment and able to complete `codex --version`;
- Python 3.11 or newer with standard-library `tomllib`;
- Git, because this contract has no archive or downloader fallback and requires an immutable exact-commit checkout;
- HTTPS access to the public GitHub repository for a read-only `git ls-remote` check.

On Windows, use `Get-Command` for command discovery. On macOS, Linux, or WSL, use `command -v`. Then run the equivalent of:

```text
codex --version
<PYTHON> --version
<PYTHON> -c "import sys, tomllib; assert sys.version_info >= (3, 11); print('PYTHON_CAPABILITY_PASS')"
git --version
git ls-remote https://github.com/SuperDaddyV/codex-sol-luna-worker.git HEAD
```

Do not treat a Codex Desktop internal application path, versioned cache directory, or content-hash directory as a supported CLI discovery mechanism. A Desktop-bundled executable satisfies this contract only when the current task environment already exposes it as a resolvable `codex` command and `codex --version` succeeds.

Display the result before any filesystem write:

```text
Sol/Luna Installation Preflight
Codex Desktop: CURRENT_SESSION / NOT_CONFIRMED
Codex CLI: PASS <version> / MISSING_OR_UNUSABLE
Python: PASS <version> / MISSING_OR_UNSUPPORTED
Git: PASS <version> / MISSING
GitHub HTTPS: PASS / BLOCKED
Ready: YES / NO
```

`Ready: YES` requires every hard prerequisite above to pass. If any item fails, set `Ready: NO`, do not create or modify files, and stop with exactly one concise remediation:

- `BLOCKED: CODEX_CLI_REQUIRED` — install or expose a supported Codex CLI yourself, reopen Codex Desktop, and retry only after `codex --version` succeeds;
- `BLOCKED: PYTHON_3_11_WITH_TOMLLIB_REQUIRED` — install a supported Python yourself, reopen the task environment, and retry;
- `BLOCKED: GIT_REQUIRED_FOR_IMMUTABLE_SOURCE` — install Git yourself, reopen the task environment, and retry;
- `BLOCKED: GITHUB_HTTPS_REQUIRED` — restore read-only HTTPS access to the public repository and retry without changing proxy or system settings automatically.

PowerShell is the native Windows shell used to run these checks, but it is not a separate cross-platform product dependency. `curl` and other download tools are not required by this contract.

## 1. Target State

The global target contains five native custom agents:

| Agent name | Model | Reasoning effort | Leaf setting |
| --- | --- | --- | --- |
| `luna_low` | `gpt-5.6-luna` | `low` | `[agents] enabled = false` |
| `luna_medium` | `gpt-5.6-luna` | `medium` | `[agents] enabled = false` |
| `luna_high` | `gpt-5.6-luna` | `high` | `[agents] enabled = false` |
| `luna_xhigh` | `gpt-5.6-luna` | `xhigh` | `[agents] enabled = false` |
| `luna_max` | `gpt-5.6-luna` | `max` | `[agents] enabled = false` |

The managed global `config.toml` block enables multi-agent work and sets `max_concurrent_threads_per_session = 3`. The managed global `AGENTS.md` block makes Sol the planner, orchestrator, ambiguity resolver, and final acceptance owner; it requires the Daily Selector, bounded Luna delegation, a Task Contract, a Context Firewall, Sol acceptance, and one concise Delegation Receipt after receipt-eligible non-trivial work. The Receipt summarizes facts already observed after the delegation decision. `Luna unavailable` is evidence-gated and requires a current-task, parent-visible selector or native-agent availability failure that arose naturally on the normal delegation path. The Receipt cannot force delegation, lower the threshold, invoke a selector, probe, tool, child, or network solely to create evidence, write state, telemetry, or repository content, or expose private reasoning.

The selector is installed at `<CODEX_HOME>/sol-luna-v4/selector.py`. Its state root is `<CODEX_HOME>/sol-luna-v4/state`. The v4 ownership manifest is `<CODEX_HOME>/sol-luna-v4/install-manifest.json`.

## 2. Explicit Non-goals

Do not install or introduce any of the following:

- Hook Router;
- `PreToolUse` enforcement;
- managed-child registry;
- daemon or background scheduler;
- database or dashboard;
- plugin framework;
- custom orchestration engine.

Do not lower the delegation threshold, force Luna use, add a Receipt-specific state or configuration flag, treat no delegation as Luna unavailability, use `Luna unavailable` as a default fallback, or treat Receipt text as runtime attestation. Stable retains the RC6 selector normalization, RC5 observability metadata, and policy UX unchanged, and adds no second selection or state authority.

Do not modify the selector algorithm, agent payloads, concurrency limit, ModelDial policy, manifest schema, migration contract, Git tag, or GitHub Release as part of setup.

## 3. Environment Discovery

Identify the runtime as native Windows, macOS, Linux, or WSL. Treat WSL as Linux with its own home and `CODEX_HOME`; do not mix WSL paths with native Windows paths.

Resolve the target in this order:

1. an explicit target approved by the user;
2. the current `CODEX_HOME` environment variable when it is explicitly set;
3. the standard user Codex home, `~/.codex`.

On native Windows, the standard expansion is the current user's `.codex` directory under the profile. On macOS, Linux, and WSL, it is `$HOME/.codex`. Resolve the absolute path locally but do not hard-code or publish a username. Confirm the path with the user if discovery produces multiple plausible targets.

Record the OS, architecture, Codex version, Python version, source commit, target path category, and whether the target already exists. Do not print credentials or full user configuration.

## 4. Python Capability

This repository requires Python 3.11 or newer and standard-library TOML support. Select `python` or `python3` based on the current environment and assign it conceptually as `<PYTHON>` for the commands below.

Run the equivalent of:

```text
<PYTHON> --version
<PYTHON> -c "import sys, tomllib; assert sys.version_info >= (3, 11); print('PYTHON_CAPABILITY_PASS')"
```

Do not install or upgrade Python. If either check fails, stop with `BLOCKED: PYTHON_3_11_WITH_TOMLLIB_REQUIRED`.

## 5. Source Acquisition

The installer source must be exactly the approved Stable Runtime Source Commit A:

```text
6a537b445ad6f17a9600c05e655f51a2844bfcc8
```

Do not substitute `master`, `main`, `origin/master`, `latest`, a floating branch, mutable `target_commitish`, or any other commit. The commit containing this setup contract is a separate documentation anchor and is not an installer source.

Git is required. After the Installation Preflight reports `Ready: YES`, create a temporary workspace outside `CODEX_HOME` and run the equivalent of:

```text
git clone --no-checkout https://github.com/SuperDaddyV/codex-sol-luna-worker.git <TEMP_SOURCE>
git -C <TEMP_SOURCE> checkout --detach 6a537b445ad6f17a9600c05e655f51a2844bfcc8
git -C <TEMP_SOURCE> rev-parse HEAD
```

Require `git rev-parse HEAD` to equal `6a537b445ad6f17a9600c05e655f51a2844bfcc8` exactly. Inspect `git status --short` and require a clean checkout before installation. Confirm `scripts/install.py` declares installer `VERSION = "v4.1.4"` before running it.

Do not execute installer code from a mutable branch. This contract defines no archive fallback. If the exact commit cannot be verified after the Git preflight passed, stop with `BLOCKED: IMMUTABLE_SOURCE_UNVERIFIED` rather than adding a downloader.

## 6. Codex Capability

The Installation Preflight has already confirmed that the `codex` command resolves and `codex --version` succeeds. The installation also requires native custom agents, multi-agent/subagent support, a primary task using GPT-5.6 Sol, and account access to GPT-5.6 Luna at `low`, `medium`, `high`, `xhigh`, and `max`.

From the verified immutable checkout, first display the capability probe plan:

```text
<PYTHON> scripts/probe_capabilities.py
```

With the user's installation authorization, run the real probe into the temporary source workspace:

```text
<PYTHON> scripts/probe_capabilities.py --execute --state <TEMP_SOURCE>/.var/setup-capabilities.json
```

The probe uses ephemeral Codex calls, ignores global user configuration, and does not edit global Codex settings. Require all five client calls to be supported. Exact echo is diagnostic; the current probe treats successful client execution as model availability. If required multi-agent behavior is absent or a required Luna effort is unavailable, stop before inspecting or writing `CODEX_HOME`; do not upgrade Codex or change authentication.

## 7. Existing State Inspection

Before writing, inspect these paths under the resolved target without printing sensitive contents:

- `config.toml`;
- `AGENTS.md` and `AGENTS.override.md`;
- `agents/`, especially the five stable Luna filenames;
- `sol-luna-v4/install-manifest.json`;
- `sol-luna-router/install-manifest.json`;
- legacy Hook definition files and scripts;
- existing v4 backup roots and any same-name files the installer would own.

Classify exactly one mode:

- **clean install**: no v4 manifest, no supported legacy manifest, and no unowned destination conflicts;
- **existing equivalent v4**: a valid v4 manifest owns equivalent payloads;
- **existing v4 upgrade**: a valid v4 manifest owns safely replaceable older payloads;
- **supported legacy migration**: no conflicting v4 installation and the legacy manifest schema is exactly `3.2`;
- **conflict**: non-empty `AGENTS.override.md`, same-name unowned agents, modified owned files, unsafe marker state, or conflicting user-owned agent settings;
- **unsupported state**: malformed or unknown manifest, ambiguous ownership, fuzzy legacy version, or an arbitrary older installation.

The presence of historical Hook files or audit bundles alone does not authorize deletion. Exact legacy `3.2` migration may remove only manifest-owned legacy Hook content. Unowned audit bundles and evidence remain preserved for review.

If classification is ambiguous, stop. Do not force an unsupported state into clean install or migration.

## 8. Dry Run

From `<TEMP_SOURCE>`, display the current help and then run the real dry-run against the explicit target:

```text
<PYTHON> scripts/install.py --help
<PYTHON> scripts/install.py --dry-run --codex-home <CODEX_HOME> --source-commit 6a537b445ad6f17a9600c05e655f51a2844bfcc8
```

Dry-run is non-mutating. Report each stable agent action (`create`, `identical`, or `conflict`), the future artifact inventory, target platform, and conflicts. Supplement it with the read-only inspection from Section 7 to summarize expected shared-file modifications, legacy removals, preserved unowned content, and the chosen mode. Do not claim that the current dry-run output is a byte-for-byte preview of every transactional merge; the apply path performs the definitive ownership validation.

Stop before apply if the dry-run returns a nonzero status, reports an unsupported platform, or reveals a conflict.

## 9. Backup

Do not create a parallel backup system with `Copy-Item`, `cp`, or hand-written archive commands. The installer's apply and uninstall paths choose `<CODEX_HOME>/backups/sol-luna-v4/<timestamp>`, snapshot every effective target and commit-marker path, record whether each path existed, hash copied bytes, and verify the inventory before writing. Any exception after verification enters the transaction rollback path before the original stable error is returned.

Capture the `backup` value returned by the installer. Treat it as the only rollback path for that transaction. If backup creation or verification fails, the installer must stop before partial installation.

## 10. Clean Install

For a classified clean install, run from the immutable checkout:

```text
<PYTHON> scripts/install.py --apply --codex-home <CODEX_HOME> --source-commit 6a537b445ad6f17a9600c05e655f51a2844bfcc8
```

The explicit target is mandatory. Do not pass `--validation-sandbox` for a real user global installation; that option only permits repository-local test targets below `.tmp/installer-validation/`.

Accept `INSTALLED` as the expected clean-install result. Record created and modified paths and the returned backup. A nonzero exit, `FAIL`, or any reason code is a blocker; do not bypass it.

## 11. Legacy v3.2 Migration

Use migration only when the read-only inspection proves that `sol-luna-router/install-manifest.json` has the exact supported schema version `3.2` and no conflicting v4 state. Run:

```text
<PYTHON> scripts/install.py --apply --migrate-v3 --codex-home <CODEX_HOME> --source-commit 6a537b445ad6f17a9600c05e655f51a2844bfcc8
```

Do not accept similar, malformed, missing, or guessed versions. The migration does not contact ModelDial, convert a legacy Daily Profile or LKG, or delete unowned audit bundles. It uses the same transaction backup, validates v4 payloads and shared merges, writes the v4 manifest last as the commit marker, and then attempts independently retryable cleanup of the old manifest.

Accept `INSTALLED` with completed cleanup as the normal result. `LEGACY_MANIFEST_CLEANUP_PENDING` means valid v4 content committed but old-manifest cleanup is incomplete; report it precisely and do not declare full installation complete until an idempotent authorized rerun completes that cleanup. Any pre-commit failure must roll back exactly.

## 12. Existing v4

For a valid installer-owned v4 installation, run the same apply command without `--migrate-v3`:

```text
<PYTHON> scripts/install.py --apply --codex-home <CODEX_HOME> --source-commit 6a537b445ad6f17a9600c05e655f51a2844bfcc8
```

Interpret the real result:

- `IDEMPOTENT_PASS`: payload and manifest are already equivalent; zero effective changes and no new backup;
- `UPGRADED`: installer-owned payload changed safely; retain the returned transaction backup;
- `LEGACY_CLEANUP_COMPLETED`: an already committed supported migration finished pending old-manifest cleanup;
- `LEGACY_MANIFEST_CLEANUP_PENDING`: cleanup remains incomplete and must be reported;
- `FAIL` with an ownership, marker, config, manifest, target, or backup reason code: stop without manual repair.

Do not use `--migrate-v3` merely because historical files remain beside a valid v4 installation.

For v4.1.4 Stable, the directly validated upgrade baseline is a repository
fake-home v4.1.3 installation. Dry-run and apply must report exactly two
effective changes: `sol-luna-v4/selector.py` and
`sol-luna-v4/install-manifest.json`. Apply must create and verify one normal
transaction backup; the second apply must be a zero-write, zero-backup current
installation result; exact rollback must restore the v4.1.3 fake-home tree.
If the previously owned v4.1.3 selector differs from its manifest hash, both
dry-run and apply must fail closed with `OWNERSHIP_CONFLICT` and make no change.
No real Global v4.1.4 transaction result is claimed by this contract.

The installed selector, installer-managed Global `AGENTS.md` block, five Luna
agents, `config.toml`, Daily Profile, LKG, lock, and unrelated user
configuration are protected unless the installer explicitly reports an owned
Stable change. If the dry-run reports any other effective change, stop before
apply. Do not create a parallel backup system or hand-edit the two expected
files. The v4.1.3 Stable entry and its historical runtime evidence remain separate and
immutable; the installer does not create or modify a Git tag or GitHub Release.

An existing valid `v4.1.0-rc5` installation remains a historical migration
case. Do not infer Stable runtime results from that older boundary. If a
valid same-day Profile or LKG already exists, reuse it without refresh, backfill,
rewrite, state migration, or ref-cost network access. `OLD_SAME_DAY_PROFILE_FORCE_REFRESH = NO`;
`STATE_MIGRATION_REQUIRED = NO`.

## 13. ModelDial / Daily Selector

The installer copies the selector but does not need live ModelDial access and does not create selector state. First actual selection occurs when the installed global policy invokes:

```text
<PYTHON> <CODEX_HOME>/sol-luna-v4/selector.py --state-dir <CODEX_HOME>/sol-luna-v4/state --ensure-daily --print-role
```

The selector requires the canonical five efforts, chooses the highest score, and breaks a tie toward the lower effort. If invoked with a restricted `--supported` set, it can choose the best locally supported alternative and record capability degradation. The normal installation capability gate requires all five efforts, so the installed policy uses the complete default set.

Selection occurs once per Beijing calendar day. A valid same-day Profile, including an RC5-created Profile using the same schema, is reused byte-for-byte without a new live fetch. On a new day, the selector tries the anonymous official ModelDial API v1 endpoint, then the official full snapshot JSON, then a valid last-known-good record. API schemas `1.0` and `1.1` are accepted; schema `1.1` deliberately consumes only the backward-compatible backend `rankings` axis and requires internally consistent backend score identity. The selector does not consume `overallRankings`, capability publications, the change feed, or advisory Agent Profiles. A valid API response stops acquisition; sources are never merged, and v4.1 has no Radar HTML runtime fallback. First use with neither valid live data nor valid fallback fails closed with `NO_LUNA_PROFILE_AVAILABLE`. `ultra` is never allowed. Do not write a particular day's score into configuration or documentation as a permanent fact.

Stable preserves the existing `--print-role` contract and the RC5/RC6 structured selection metadata:

```text
<PYTHON> <CODEX_HOME>/sol-luna-v4/selector.py --state-dir <CODEX_HOME>/sol-luna-v4/state --ensure-daily --print-selection
```

Historical Stable evidence includes valid role/effort proofs, but the v4.1.4
source and fake-home evidence adds no current real installed-runtime proof. Do
not record a specific day's selected effort in public documentation or infer a
Daily selection write from repository validation.

The saved selection is the single source for delegated Receipt suffixes. `Luna ref-cost ↓X.X%` is an optional ModelDial configuration reference-cost comparison from the same comparable batch, pricing snapshot, provider, route, and selected effort for Sol and Luna. It does not measure actual token savings, actual billing savings, subscription quota savings, or whole-task savings. If reference-cost metadata is missing, invalid, or non-comparable, omit only that suffix; selection and delegation continue normally.

Append `LKG` only when the saved selection used fallback. Append `capability <source_effort>→<selected_effort>` only when local capability forced a lower selected effort. Receipt generation performs no additional selector, network, state, capability-probe, or child work.

## 14. Read-only Status and Diagnostic

The natural-language request `检查 Sol/Luna 状态` runs the installed selector once with `--status-json`. It is strictly read-only:

```text
STATUS_NETWORK = 0
STATUS_SELECTOR_LOCK = 0
STATUS_STATE_WRITES = 0
STATUS_LUNA_SPAWN = 0
```

Health classification must preserve these distinctions:

- Profile missing → `Healthy / TODAY_SELECTION_NOT_INITIALIZED`;
- Profile content invalid → `Unavailable / DAILY_PROFILE_INVALID`;
- Profile read failure → `Misconfigured / DAILY_PROFILE_READ_FAILED`.

A local read failure is never reported as Luna unavailable. Overall health precedence remains `Misconfigured > Unavailable > Degraded > Healthy`.

The natural-language request `生成 Sol/Luna 诊断报告` uses the same single read-only `--status-json` result. Its fixed whitelist is limited to schema and generation metadata; OS, architecture, Codex, Python, installed version, and verified source SHA; manifest, Global policy, selector, agent, native-leaf, configuration, and parallel-limit status; Beijing-day selection, selected role and effort, source, fallback, capability, snapshot identifiers, and optional ref-cost status; project override status; health and reason codes; and symbolic sanitized locations. It must not expose full configuration, full `AGENTS.md`, environment variables, credentials, logs, child reasoning, real private paths, private remote URLs, exception text, or arbitrary file content.

## 15. Upgrade to the Latest Published Version

The natural-language request `升级 Sol/Luna 到最新版本` means the latest published project Release, including Stable and prerelease versions. Release discovery is outside the installer. Consider only published, non-draft Releases with strict project SemVer; validate the prerelease flag, reject malformed or duplicate normalized versions, and select by SemVer precedence rather than publication time.

Before any prerelease apply, show a clear prerelease / Public Beta risk notice. Resolve the immutable Release tag to an exact commit SHA, detect tag movement, check out that commit detached, and verify the installer version and setup/source alignment. Pass the verified immutable SHA to the transactional installer through `--source-commit`; never execute from a branch or mutable `target_commitish`. Preserve ownership validation, transaction backup, apply verification, rollback, uninstall, no-downgrade behavior, and zero-write idempotency.

This installed-policy feature does not authorize the current setup run to
replace the approved Stable Source Commit A. Every Stable installer
command in this contract remains pinned to
`6a537b445ad6f17a9600c05e655f51a2844bfcc8`; a published Stable command must
be sourced from its separately reviewed immutable Release chain.

## 16. Validation

Before apply, validate the immutable source checkout:

```text
<PYTHON> -m unittest discover -s tests -v
```

After apply, perform read-only inspection and require all of the following:

1. the five expected files exist under `<CODEX_HOME>/agents/`;
2. every agent TOML parses, has the expected name, `gpt-5.6-luna`, matching effort, and `[agents] enabled = false`;
3. `config.toml` parses and the managed v4 block enables agents with maximum direct concurrency 3;
4. the managed v4 block exists exactly once in `AGENTS.md`, contains the installed absolute selector and state command, and includes the non-trivial-task Delegation Receipt policy without forcing delegation or extra Receipt work;
5. the selector file compiles and its `--help` command succeeds;
6. `sol-luna-v4/install-manifest.json` parses, reports `v4.1.4`, records source commit `6a537b445ad6f17a9600c05e655f51a2844bfcc8`, and records the expected owned files and blocks;
7. installer-reported created, modified, removed, and preserved content matches the selected mode;
8. no active configuration or Hook definition still invokes the legacy Sol/Luna Router.

Historical directories, trusted metadata, backups, or audit evidence may remain without being runtime dependencies. Do not delete them during validation. Do not expose unrelated configuration values in the report.

### v4.1.4 Stable source and fake-home evidence

Stable Source Commit A `6a537b445ad6f17a9600c05e655f51a2844bfcc8`
passed exact-SHA CI run `33264634602` on Windows, Ubuntu, and macOS; each
platform reported `366` tests all `PASS`.

Repository fake-home lifecycle tests cover v4.1.3-to-v4.1.4 dry-run, apply,
two-file ownership scope, transaction backup, second-apply idempotency, exact
rollback, and modified-owned-selector conflict with zero writes. Uninstall tests
cover verified-backup failure with no tree change and an exception after one
effective operation with exact rollback. Read-only live checks on 2026-08-30
exercised the current ModelDial API v1.1 response and the
Full Snapshot fallback independently; both selected the backend-axis result and
projected the same comparable reference-cost metadata. Live values can change
and are not embedded as a permanent installation promise.

This evidence is repository, fake-home, and read-only network validation. It is
not a real Global v4.1.4 installer apply, real authentication test, Daily state
write, candidate fresh-task smoke, or universal compatibility claim. This
contract does not by itself establish a tag or GitHub Release; publication
requires the separately verified immutable `v4.1.4` tag and non-draft,
non-prerelease Release.

### Historical v4.1.3 Stable evidence

Stable Source Commit A `71894e2ef5007c9ba3e6f9d9efbf91cbdad302b4`
passed exact-SHA CI run `33253340074` on Windows, Ubuntu, and macOS; the run
reported `363` tests all `PASS`. No real Global v4.1.3 installer apply or
candidate fresh-task smoke was claimed.

### Historical v4.1.2 Stable evidence

Candidate Source Commit A `551520c2435aca94d60132f292edbd53cc975cbe`
passed exact-SHA CI run `32717295801` on Windows, Ubuntu, and macOS; the run
reported `357` tests all `PASS`. Current-master evidence commit
`fac118ac5ca096aaf1ef8d68b79bfc1372998a5a` passed CI run `32717520585` on the
same three source-validation platforms. The current-master evidence commit is
not Source Commit A and is not an alternate installer identity.

The recorded Stable transaction began from a real Global `v4.1.0-rc6`
baseline whose source was `50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49`. From a
detached exact Source A checkout, the dry-run was `DRY_RUN_PASS` with
`writes NO`, `effective_changes 2`, and five-effort capability `PASS`. Apply
was `UPGRADED` with `configuration_preserved true`, `effective_changes 2`,
only the selector and install manifest changed, and one transaction backup.
Second apply was `CURRENT_INSTALLATION_PASS` with `writes NO`,
`effective_changes 0`, and `backup NONE`.

Daily selector proof returned a legal role and matching effort. The specific
day's effort is intentionally omitted; same-day Profile and LKG were not
rewritten. Exactly one fresh-task compatibility smoke ran for about `169.4`
seconds with `codex-cli 0.146.0`, exited `0`, and passed `CLI`, `Luna
capability`, `Selector`, `Delegation`, `Protected state`, `Runtime contract`,
and final `Compatibility`. Pre/post protected hashes for `AGENTS.md`,
configuration, the five agents, selector, manifest, Profile, LKG, and lock were
unchanged, and the smoke created no backup.

This evidence is limited to one native Windows Codex environment. Windows,
Ubuntu, and macOS CI validate repository source only; they are not three-platform
real-runtime evidence. This contract does not by itself establish a tag or
GitHub Release; publication requires the separately verified immutable
`v4.1.2` tag and non-draft, non-prerelease Release.

Stable Source Commit A2 local repository tests and its Windows / Ubuntu / macOS exact-SHA CI `PASS` are repository validation only. The `v4.1.0`→`v4.1.1` fake-home lifecycle verifies that only the ownership manifest changes. No real Global `v4.1.1` installer apply was performed. In the documented native Windows Codex environment, RC6 acceptance remains historical evidence and the independent one-run `v4.1.1` pre-publication compatibility smoke passed against the unchanged installed product runtime:

- O1 Natural-language healthy status — `PASS`;
- O2 No-profile healthy status — `PASS`;
- O3 Degraded LKG Receipt and status — `PASS`;
- O4 Capability-degraded selected-effort Receipt and status — `PASS`;
- O5 Unavailable evidence status — `PASS`;
- O6 Misconfigured precedence — `PASS`;
- O7 Safe diagnostic report — `PASS`;
- O8 Latest prerelease immutable discovery and notice — `PASS`;
- O9 Fail-soft observability selection, status, and Receipt omission — `PASS`;
- O10 Fresh-session delegation and Receipt suffixes — `PASS`.

RC6 real Global upgrade, idempotency, and rollback readiness remain separate
acceptance operation, not O9. The recorded upgrade returned `UPGRADED`, changed
only the installed selector and ownership manifest, and was followed by
`IDEMPOTENT_PASS`; the installer-owned rollback snapshot exists under the owned
backup root and its snapshot hashes verify. Final O4/O9 re-certification passed
through the isolated acceptance harness. The harness attributed runtime writes
only to its isolated home, observed no unknown runtime path, left the real
protected Sol/Luna state and root identity unchanged, and removed every owned
acceptance artifact.

This is environment- and scenario-bounded evidence from one native Windows
Codex Desktop/CLI environment. It is not three-platform real-runtime evidence
or a universal compatibility claim. Stable publication remains a separate
immutable tag and GitHub Release fact.

## 17. Fresh Session Requirement

Codex loads global and project instructions when a run or task starts. Updating `AGENTS.md`, agent TOML, `config.toml`, or the selector does not make an already-open task reliable evidence of the new effective configuration.

After install or upgrade:

1. finish the installer report;
2. fully reload Codex Desktop/App Server when appropriate for the client;
3. run the installed selector exactly once with `--ensure-daily --print-selection` and require exit code `0`, one allowed `selected_role`, and the matching `selected_effort`;
4. start a separate new Codex task in the intended scope;
5. perform the compatibility smoke there exactly once.

After rollback or uninstall, finish the report, reload Codex, and start a new task; Daily selection initialization is not an uninstall or rollback requirement.

Do not require an operating-system reboot unless an independently verified system issue requires it. This project itself does not require a Windows reboot.

## 18. Runtime Smoke Test

Before opening the fresh task, Daily selection proof must already exist. The compatibility smoke is deliberately status-only and must not initialize selector state. In the fresh task, run from the verified Stable Source Commit A checkout:

```text
<PYTHON> scripts/compatibility_smoke.py --codex-home <CODEX_HOME>
```

Run the command once and give the original process sufficient time to finish; 30 seconds without output is not failure by itself. Require `CLI`, `Luna capability`, `Selector`, `Delegation`, `Protected state`, `Runtime contract`, and final `Compatibility` all to report `PASS`. Any `BLOCKED`, `FAIL`, `REVIEW REQUIRED`, timeout, nonzero exit, or incomplete evidence stops without automatic retry.

The smoke implements the following concise user-facing checks rather than reproducing the development G1-G7 protocol:

1. confirm the five global Luna role names are discoverable in the effective context;
2. run the installed selector command and require exactly one allowed role;
3. explicitly delegate a bounded exact-echo task through that selected native role and inspect parent-visible agent metadata;
4. give Sol a second clearly bounded task without naming a role and verify policy-based delegation when Sol judges it worthwhile;
5. confirm the Luna child has no multi-agent/delegation tools because it is a native leaf;
6. require Sol to review the child evidence and own the final conclusion.

The recorded RC4 release acceptance used four fresh-task cases after a separately authorized real upgrade; those historical results did not establish RC6 runtime acceptance. RC6 independently passed the same matrix in the documented environment before becoming the Stable runtime payload: Case A had zero direct children and the reasoning/architecture Receipt; Case B used two actual direct Luna children with parent-visible parallel overlap and zero grandchildren; Case C had zero children, no availability evidence, and the no-independent-work Receipt; controlled Case D produced `NO_LUNA_PROFILE_AVAILABLE` from isolated state and verified both the positive evidence gate and the negative no-evidence prohibition. Apply the same evidence requirements when validating every future installation: Runtime Case A is a non-trivial architecture or reasoning task; require zero direct children and `Sol/Luna: Sol-only · reasoning/architecture task`. Runtime Case B contains two or three independent bounded read-only checks; require actual Luna direct children, an actual role and count matching `Sol/Luna: delegated · <role> ×<direct_child_count>`, and `parallel` only when parent-visible evidence proves execution overlap. Runtime Case C is non-trivial, non-architecture, sequential or tightly coupled work with no clean independent bounded child task; require no availability failure evidence, zero children, selector invocation only if normal execution required it, and `Sol/Luna: Sol-only · no independent bounded work`; `Luna unavailable` is forbidden. Runtime Case D exercises a real-unavailable classification only in a controlled fixture, fake `CODEX_HOME`, test harness, or non-production simulation where the normal path already exposes the failure. Do not damage or reconfigure the real selector, state, account, or Global environment to manufacture evidence.

In all four cases, the Receipt is only a user-facing summary; verify child absence, presence, and availability facts with parent-visible runtime metadata. Receipt generation itself must not invoke a selector, capability probe, tool, child, network, state write, telemetry, or repository write. Do not accept Receipt text by itself as proof. The recorded RC4 and RC6 acceptance runs each passed all four cases in their own environments; Stable preserves the accepted RC6 product runtime, but every new installation or upgrade must still complete its own fresh-task smoke test before returning `INSTALL_RUNTIME_PASS`.

Return `INSTALL_RUNTIME_PASS` only when all applicable checks pass. Otherwise return the exact failed step and evidence boundary. A sentinel string by itself is not proof of model, role, or leaf behavior. Static CI and repository tests are not substitutes for this fresh-task runtime check.

## 19. Rollback

Rollback is available only with the exact backup path returned by the relevant successful install or upgrade. Require the path to remain under `<CODEX_HOME>/backups/sol-luna-v4/`, then run from the same immutable source:

```text
<PYTHON> scripts/install.py --rollback <BACKUP_PATH> --codex-home <CODEX_HOME>
```

Accept only `ROLLBACK_EXACT_PASS`. The installer verifies the snapshot hashes, restores files that existed, removes transaction-created files, restores the prior target existence state when applicable, and removes the consumed backup after success. Do not hand-edit TOML or copy selected files as a substitute. Reload Codex and start a new task after rollback.

## 20. Uninstall

The current public CLI supports manifest-owned uninstall:

```text
<PYTHON> scripts/install.py --uninstall --codex-home <CODEX_HOME>
```

Uninstall requires a valid v4 manifest. It verifies hashes for owned files and marker blocks, creates and verifies a transaction backup before modifying any managed path, removes only owned content, restores surrounding user files by removing the managed blocks, and preserves unrelated agents and runtime state. Any exception after backup verification enters exact rollback before the original stable error is returned. If owned content changed, the backup cannot be verified, or the manifest is absent or invalid, it fails closed. Accept only `UNINSTALLED`, then reload Codex and start a new task.

Uninstall is not the same as transaction rollback: it removes the installed v4 ownership set rather than restoring a specific pre-install snapshot.

## 21. Final Report

Return a concise report in this exact structure without secrets or raw user configuration:

```text
【Environment】
OS：
Codex：
Python：
source commit：
CODEX_HOME：confirmed / blocked

【Mode】
clean install / existing equivalent v4 / existing v4 upgrade / legacy 3.2 migration / blocked

【Dry Run】
status：
create：
modify：
remove：
preserve：
conflicts：

【Backup】
created：YES / NO
rollback path：recorded securely / none

【Installed】
status：
owned payloads：

【Preserved】
user configuration：
legacy evidence：

【Daily Selector】
static validation：
fresh-day result：

【Observability】
status：read-only / exact blocker
diagnostic：sanitized / exact blocker
ref-cost：comparable suffix / omitted

【Runtime Smoke】
fresh task：
result：INSTALL_RUNTIME_PASS / exact blocker

【Rollback Available】
YES / NO

【Final Status】
INSTALL_RUNTIME_PASS / BLOCKED
```

Do not claim runtime PASS before the fresh-task smoke test. If setup stops before mutation, say so explicitly. If mutation committed but runtime validation is pending, report installation and runtime as separate states.

## 22. v4.1.4 Stable assisted installation handoff

Sections 0–21 are the reviewed `v4.1.4` Stable transactional setup contract.
The separately pinned English assisted-installation contract is the default
user-facing entry and pins this Setup contract through an exact immutable
documentation commit. The README pins that assisted contract through a later
immutable documentation commit; neither documentation commit is the runtime
source or is passed to the installer. This document intentionally has no
self-referencing SHA.

Assisted recovery is limited to validated entries in
`scripts/install_recovery_catalog.json`; the transactional installer remains
the sole authority for runtime writes.

After the conversation-level bootstrap boundary has produced Python 3.11+,
Git, and a clean detached Stable Source Commit A checkout, the pinned assisted
contract uses:

```text
<PYTHON> scripts/install_assist.py check --codex-home <CODEX_HOME>
<PYTHON> scripts/install_assist.py plan --codex-home <CODEX_HOME>
<PYTHON> scripts/install_assist.py recover --codex-home <CODEX_HOME> --approve <PLAN_ID>
<PYTHON> scripts/install_assist.py install --codex-home <CODEX_HOME> --source-commit 6a537b445ad6f17a9600c05e655f51a2844bfcc8
<PYTHON> scripts/install_assist.py install --apply --codex-home <CODEX_HOME> --source-commit 6a537b445ad6f17a9600c05e655f51a2844bfcc8
```

The `install` command verifies the exact clean detached source, runs the five
ephemeral read-only Luna capability checks, and only then calls the existing
installer dry-run. Without `--apply`, it stops at `DRY_RUN`. After explicit
apply authorization, the same command with `--apply` may delegate writes,
backup, ownership, rollback, migration, and uninstall behavior exclusively to
`scripts/install.py`. An `IDEMPOTENT_PASS` current installation remains a
zero-write, zero-backup fast path, but it enters the same explicit
`SELECTOR_INITIALIZATION` gate as an applied installation. After any required
Codex reload, run exactly:

```text
<PYTHON> <CODEX_HOME>/sol-luna-v4/selector.py --state-dir <CODEX_HOME>/sol-luna-v4/state --ensure-daily --print-selection
```

Require exit code `0`, one of `luna_low`, `luna_medium`, `luna_high`,
`luna_xhigh`, or `luna_max` in `selected_role`, and the matching
`selected_effort`. This explicit normal selector operation may create or reuse
the Beijing-day selection. A failure or incomplete proof stops without an
automatic retry. Only after PASS may a separate new task run the one allowed
fresh-task compatibility smoke. The smoke remains read-only and status-only; it
must not initialize Daily selection or use `--ensure-daily`.

P3 standalone bootstrap remains out of scope.
