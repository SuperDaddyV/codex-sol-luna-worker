# Codex Sol + Luna Worker — Execution Setup Contract

Status: `v4.1.0-rc4` source candidate for the Receipt reason evidence-gating fix; it is not published and has not run fresh-session runtime acceptance. `v4.1.0-rc3` remains the current published preview prerelease, and `v4.0.0` remains the current stable release.

> [!IMPORTANT]
> This is an independent community project. It is not affiliated with, sponsored by, or endorsed by OpenAI or ModelDial. The user must review this contract before execution. Prefer the immutable commit-pinned raw URL published in the project README. Never silently expand permissions, installation scope, or network access.

This document is an execution contract for Codex, not a replacement installer. Orchestrate `scripts/install.py`; do not reproduce its merge, ownership, backup, migration, rollback, or uninstall logic with ad hoc shell commands.

## 0. Document Role

You are the installation agent. Your job is to inspect, plan, back up through the installer, install, validate, and report. Preserve an evidence-based boundary between repository checks and real runtime checks.

You must:

1. obtain the exact immutable source commit associated with this contract;
2. discover the current OS, Python, Codex, and target `CODEX_HOME` without guessing;
3. inspect existing state without exposing unrelated private content;
4. run the existing installer dry-run before any mutation;
5. classify the installation mode and stop on uncertainty;
6. use the existing installer transaction for apply, migration, rollback, and uninstall;
7. validate static payloads and then require a fresh Codex task for runtime smoke testing;
8. report what was changed, preserved, backed up, or blocked.

You must not guess paths, overwrite unknown configuration, install system dependencies, change authentication, update Codex, move Git tags, execute mutable `master` content, bypass ownership checks, or silently widen permissions. If a required condition is missing, stop with `BLOCKED` and the exact reason.

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

Do not lower the delegation threshold, force Luna use, add a Receipt-specific state or configuration flag, treat no delegation as Luna unavailability, use `Luna unavailable` as a default fallback, or treat Receipt text as runtime attestation. Selector, agent, configuration, state, concurrency, and legacy migration behavior remain unchanged in RC4.

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

## 5. Codex Capability

Confirm that a Codex client is available and record `codex --version`. The installation requires native custom agents, multi-agent/subagent support, a primary task using GPT-5.6 Sol, and account access to GPT-5.6 Luna at `low`, `medium`, `high`, `xhigh`, and `max`.

From the immutable checkout, first display the capability probe plan:

```text
<PYTHON> scripts/probe_capabilities.py
```

With the user's installation authorization, run the real probe into the temporary source workspace:

```text
<PYTHON> scripts/probe_capabilities.py --execute --state <TEMP_SOURCE>/.var/setup-capabilities.json
```

The probe uses ephemeral Codex calls, ignores global user configuration, and does not edit global Codex settings. Require all five client calls to be supported. Exact echo is diagnostic; the current probe treats successful client execution as model availability. If the Codex command is unavailable, required multi-agent behavior is absent, or a required Luna effort is unavailable, do not upgrade Codex or change authentication. Stop and report the exact capability blocker.

## 6. Source Acquisition

The installer source must be the same immutable commit as this setup contract. Define `<SETUP_COMMIT>` as the 40-character hexadecimal commit in the raw URL from which the user asked you to read this document. If the contract came from a local file and no approved commit can be proven, stop and ask for an immutable commit; do not substitute `master`, `latest`, or a release tag that does not contain this file.

When Git is available, create a temporary workspace outside `CODEX_HOME` and run the equivalent of:

```text
git clone https://github.com/SuperDaddyV/codex-sol-luna-worker.git <TEMP_SOURCE>
git -C <TEMP_SOURCE> checkout --detach <SETUP_COMMIT>
git -C <TEMP_SOURCE> rev-parse HEAD
```

Require `git rev-parse HEAD` to equal `<SETUP_COMMIT>` exactly. Confirm that `<TEMP_SOURCE>/CODEX_SOL_LUNA_SETUP.md` exists and matches the retrieved contract. Inspect `git status --short` and require a clean checkout before installation.

Do not execute installer code from a mutable branch. This contract defines no archive fallback; if Git or exact commit verification is unavailable, stop with `BLOCKED: IMMUTABLE_SOURCE_UNVERIFIED` rather than adding a downloader.

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
<PYTHON> scripts/install.py --dry-run --codex-home <CODEX_HOME>
```

Dry-run is non-mutating. Report each stable agent action (`create`, `identical`, or `conflict`), the future artifact inventory, target platform, and conflicts. Supplement it with the read-only inspection from Section 7 to summarize expected shared-file modifications, legacy removals, preserved unowned content, and the chosen mode. Do not claim that the current dry-run output is a byte-for-byte preview of every transactional merge; the apply path performs the definitive ownership validation.

Stop before apply if the dry-run returns a nonzero status, reports an unsupported platform, or reveals a conflict.

## 9. Backup

Do not create a parallel backup system with `Copy-Item`, `cp`, or hand-written archive commands. The installer's apply path chooses `<CODEX_HOME>/backups/sol-luna-v4/<timestamp>`, snapshots every effective target and commit-marker path, records whether each path existed, hashes copied bytes, and verifies the inventory before writing.

Capture the `backup` value returned by the installer. Treat it as the only rollback path for that transaction. If backup creation or verification fails, the installer must stop before partial installation.

## 10. Clean Install

For a classified clean install, run from the immutable checkout:

```text
<PYTHON> scripts/install.py --apply --codex-home <CODEX_HOME>
```

The explicit target is mandatory. Do not pass `--validation-sandbox` for a real user global installation; that option only permits repository-local test targets below `.tmp/installer-validation/`.

Accept `INSTALLED` as the expected clean-install result. Record created and modified paths and the returned backup. A nonzero exit, `FAIL`, or any reason code is a blocker; do not bypass it.

## 11. Legacy v3.2 Migration

Use migration only when the read-only inspection proves that `sol-luna-router/install-manifest.json` has the exact supported schema version `3.2` and no conflicting v4 state. Run:

```text
<PYTHON> scripts/install.py --apply --migrate-v3 --codex-home <CODEX_HOME>
```

Do not accept similar, malformed, missing, or guessed versions. The migration does not contact ModelDial, convert a legacy Daily Profile or LKG, or delete unowned audit bundles. It uses the same transaction backup, validates v4 payloads and shared merges, writes the v4 manifest last as the commit marker, and then attempts independently retryable cleanup of the old manifest.

Accept `INSTALLED` with completed cleanup as the normal result. `LEGACY_MANIFEST_CLEANUP_PENDING` means valid v4 content committed but old-manifest cleanup is incomplete; report it precisely and do not declare full installation complete until an idempotent authorized rerun completes that cleanup. Any pre-commit failure must roll back exactly.

## 12. Existing v4

For a valid installer-owned v4 installation, run the same apply command without `--migrate-v3`:

```text
<PYTHON> scripts/install.py --apply --codex-home <CODEX_HOME>
```

Interpret the real result:

- `IDEMPOTENT_PASS`: payload and manifest are already equivalent; zero effective changes and no new backup;
- `UPGRADED`: installer-owned payload changed safely; retain the returned transaction backup;
- `LEGACY_CLEANUP_COMPLETED`: an already committed supported migration finished pending old-manifest cleanup;
- `LEGACY_MANIFEST_CLEANUP_PENDING`: cleanup remains incomplete and must be reported;
- `FAIL` with an ownership, marker, config, manifest, target, or backup reason code: stop without manual repair.

Do not use `--migrate-v3` merely because historical files remain beside a valid v4 installation.

An existing valid `v4.1.0-rc3` installation is an existing v4 upgrade for RC4. The expected effective payload change is the installer-managed Global `AGENTS.md` block plus manifest version and ownership metadata. The selector, five Luna agents, `config.toml` managed values, Daily Profile, LKG, state schema, and migration behavior must remain byte-preserved. The installer must create and verify its normal transaction backup before applying the managed block change.

## 13. ModelDial / Daily Selector

The installer copies the selector but does not need live ModelDial access and does not create selector state. First actual selection occurs when the installed global policy invokes:

```text
<PYTHON> <CODEX_HOME>/sol-luna-v4/selector.py --state-dir <CODEX_HOME>/sol-luna-v4/state --ensure-daily --print-role
```

The selector requires the canonical five efforts, chooses the highest score, and breaks a tie toward the lower effort. If invoked with a restricted `--supported` set, it can choose the best locally supported alternative and record capability degradation. The normal installation capability gate requires all five efforts, so the installed policy uses the complete default set.

Selection occurs once per Beijing calendar day. A valid same-day profile is reused without a new live fetch. On a new day, the selector tries the anonymous official ModelDial API v1 endpoint, then the official full snapshot JSON, then a valid last-known-good record. A valid API response stops acquisition; sources are never merged, and v4.1 has no Radar HTML runtime fallback. First use with neither valid live data nor valid fallback fails closed with `NO_LUNA_PROFILE_AVAILABLE`. `ultra` is never allowed. Do not write a particular day's score into configuration or documentation as a permanent fact.

## 14. Validation

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
6. `sol-luna-v4/install-manifest.json` parses, reports `v4.1.0-rc4`, and records the expected owned files and blocks;
7. installer-reported created, modified, removed, and preserved content matches the selected mode;
8. no active configuration or Hook definition still invokes the legacy Sol/Luna Router.

Historical directories, trusted metadata, backups, or audit evidence may remain without being runtime dependencies. Do not delete them during validation. Do not expose unrelated configuration values in the report.

## 15. Fresh Session Requirement

Codex loads global and project instructions when a run or task starts. Updating `AGENTS.md`, agent TOML, `config.toml`, or the selector does not make an already-open task reliable evidence of the new effective configuration.

After install, upgrade, rollback, or uninstall:

1. finish the installer report;
2. fully reload Codex Desktop/App Server when appropriate for the client;
3. start a new Codex task in the intended scope;
4. perform the runtime smoke test there.

Do not require an operating-system reboot unless an independently verified system issue requires it. This project itself does not require a Windows reboot.

## 16. Runtime Smoke Test

In the fresh task, use a concise user-facing smoke test rather than reproducing the development G1-G7 protocol:

1. confirm the five global Luna role names are discoverable in the effective context;
2. run the installed selector command and require exactly one allowed role;
3. explicitly delegate a bounded exact-echo task through that selected native role and inspect parent-visible agent metadata;
4. give Sol a second clearly bounded task without naming a role and verify policy-based delegation when Sol judges it worthwhile;
5. confirm the Luna child has no multi-agent/delegation tools because it is a native leaf;
6. require Sol to review the child evidence and own the final conclusion.

RC4 runtime acceptance must add four fresh-task cases after a separately authorized real upgrade. Runtime Case A is a non-trivial architecture or reasoning task: require zero direct children and `Sol/Luna: Sol-only · reasoning/architecture task`. Runtime Case B contains two or three independent bounded read-only checks: require actual Luna direct children, an actual role and count matching `Sol/Luna: delegated · <role> ×<direct_child_count>`, and `parallel` only when parent-visible evidence proves execution overlap. Runtime Case C is non-trivial, non-architecture, sequential or tightly coupled work with no clean independent bounded child task: require no availability failure evidence, zero children, selector invocation only if normal execution required it, and `Sol/Luna: Sol-only · no independent bounded work`; `Luna unavailable` is forbidden. Runtime Case D exercises a real-unavailable classification only in a controlled fixture, fake `CODEX_HOME`, test harness, or non-production simulation where the normal path already exposes the failure. Do not damage or reconfigure the real selector, state, account, or Global environment to manufacture evidence.

In all four cases, the Receipt is only a user-facing summary; verify child absence, presence, and availability facts with parent-visible runtime metadata. Receipt generation itself must not invoke a selector, capability probe, tool, child, network, state write, telemetry, or repository write. Do not accept Receipt text by itself as proof. RC4 fresh-session runtime acceptance remains `NOT RUN` while this document describes a source candidate.

Return `INSTALL_RUNTIME_PASS` only when all applicable checks pass. Otherwise return the exact failed step and evidence boundary. A sentinel string by itself is not proof of model, role, or leaf behavior. Static CI and repository tests are not substitutes for this fresh-task runtime check.

## 17. Rollback

Rollback is available only with the exact backup path returned by the relevant successful install or upgrade. Require the path to remain under `<CODEX_HOME>/backups/sol-luna-v4/`, then run from the same immutable source:

```text
<PYTHON> scripts/install.py --rollback <BACKUP_PATH> --codex-home <CODEX_HOME>
```

Accept only `ROLLBACK_EXACT_PASS`. The installer verifies the snapshot hashes, restores files that existed, removes transaction-created files, restores the prior target existence state when applicable, and removes the consumed backup after success. Do not hand-edit TOML or copy selected files as a substitute. Reload Codex and start a new task after rollback.

## 18. Uninstall

The current public CLI supports manifest-owned uninstall:

```text
<PYTHON> scripts/install.py --uninstall --codex-home <CODEX_HOME>
```

Uninstall requires a valid v4 manifest. It verifies hashes for owned files and marker blocks, removes only owned content, restores surrounding user files by removing the managed blocks, and preserves unrelated agents and runtime state. If owned content changed or the manifest is absent or invalid, it fails closed. Accept only `UNINSTALLED`, then reload Codex and start a new task.

Uninstall is not the same as transaction rollback: it removes the installed v4 ownership set rather than restoring a specific pre-install snapshot.

## 19. Final Report

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

【Runtime Smoke】
fresh task：
result：INSTALL_RUNTIME_PASS / exact blocker

【Rollback Available】
YES / NO

【Final Status】
INSTALL_RUNTIME_PASS / BLOCKED
```

Do not claim runtime PASS before the fresh-task smoke test. If setup stops before mutation, say so explicitly. If mutation committed but runtime validation is pending, report installation and runtime as separate states.
