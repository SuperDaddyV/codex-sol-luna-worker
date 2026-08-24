# Sol/Luna v4.1.0 Assisted Installation Contract

Assistance contract version: `1`.

This document is the user-facing recovery wrapper for the published `v4.1.0`
Stable installation. It improves prerequisite diagnosis and recovery; it does
not change the Stable runtime payload, installer, setup contract, tag, or
Release.

## 1. Immutable target

Use only these reviewed identities:

- Stable release: `v4.1.0`;
- Stable runtime source commit:
  `67a72f8accc5d53ef04ff8d64d8838e397ceecda`;
- Stable setup contract documentation commit:
  `2c912b1e1a0fdbd115eb605517fde9385b633745`;
- Stable setup contract:
  `https://raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/2c912b1e1a0fdbd115eb605517fde9385b633745/CODEX_SOL_LUNA_SETUP.md`.

Never substitute mutable `master`, another branch, `target_commitish`, an
archive, or a different Release. `v4.1.0-rc6` remains an immutable historical
Prerelease / Preview / Public Beta. Do not move or rewrite any tag or Release.

## 2. Authority and success boundary

This assistance contract governs prerequisite discovery and recovery before the
Stable setup contract begins. After every hard prerequisite passes, the pinned
Stable setup contract becomes authoritative for source acquisition, capability
probing, classification, dry-run, transaction backup, installation, rollback,
and validation.

The pasted installation request authorizes read-only diagnosis and the safe
session-only remediations defined below. It does not pre-authorize package
installation, administrator elevation, persistent environment changes, proxy or
certificate changes, authentication changes, sandbox expansion, or edits to
unrelated user configuration. Active Codex approval, sandbox, operating-system,
and organization policies remain in force.

The workflow succeeds only when installation and the required fresh-task smoke
validation complete. It otherwise ends as `NEEDS_USER_ACTION` or `BLOCKED` with
one exact next action. Never claim that every environment can be repaired
automatically, and never loop until an unsafe or unverified change appears to
work.

## 3. One-pass read-only diagnosis

Before cloning or downloading source, creating a temporary directory, writing
probe state, changing an environment variable persistently, or invoking any
installer mode, inspect all independent prerequisites in one read-only pass:

1. identify the current operating system, shell, Codex client, and whether this
   is a current Codex task;
2. run `codex --version` through normal command resolution;
3. inspect normal platform launchers for an already installed Python and verify
   Python 3.11 or newer with `tomllib`;
4. run `git --version`;
5. when Git is usable, run a read-only `git ls-remote` against
   `https://github.com/SuperDaddyV/codex-sol-luna-worker.git`;
6. read-only inspect whether a supported, trusted package manager is available
   if a hard dependency is missing.

Do not recursively search the filesystem or inspect internal Codex Desktop
application directories for executables. Do not stop at the first missing
dependency. Report all independent results; mark a dependent check as
`NOT_CHECKED (<dependency> required)` instead of presenting it as a second root
cause.

Display this summary before any recovery action:

```text
Sol/Luna Assisted Installation
Target: v4.1.0
Runtime source: 67a72f8accc5d53ef04ff8d64d8838e397ceecda
Codex CLI: PASS <version> / MISSING_OR_UNUSABLE
Python: PASS <version> / MISSING_OR_UNSUPPORTED
Git: PASS <version> / MISSING
GitHub HTTPS: PASS / BLOCKED / NOT_CHECKED (Git required)
Recovery: NONE / SAFE / AWAITING_APPROVAL / NEEDS_USER_ACTION
Ready: YES / NO
```

`Ready: YES` still requires every hard prerequisite in the pinned Stable setup
contract. Diagnosis aggregation improves the report; it does not weaken a gate.

## 4. Safe automatic recovery

Without further approval, Codex may perform only these no-write or session-only
actions:

- select an already installed, supported Python through normal platform
  launchers and use that exact executable as `<PYTHON>` for this task;
- select an already installed Git or Codex CLI already exposed through normal
  command resolution;
- refresh only the current process from environment values that the user or an
  official installer already persisted; do not create or persist a new `PATH`
  entry;
- correct command quoting, shell syntax, and executable selection without
  changing project or user files;
- retry a read-only GitHub HTTPS check only when the failure is plausibly
  transient, subject to Section 7.

After a safe action, rerun the failed check and any checks that depended on it.
Do not describe discovery of an existing usable tool as a package installation.

## 5. Approval-required recovery

When Python, Git, or the Codex CLI is genuinely missing or unusable, prepare one
combined recovery proposal. Before asking for approval:

1. obtain current installation guidance from official OpenAI documentation for
   the Codex CLI and from the operating-system or tool vendor for Python, Git,
   and the package manager;
2. identify the exact command, package identity, source, install scope, whether
   administrator elevation is required, persistent changes, and the
   uninstall/rollback route;
3. prefer a current-user install when it satisfies the prerequisite and does
   not weaken security;
4. do not use an unverified third-party bootstrap script or a `curl | sh` /
   equivalent pipeline.

Show the proposal in this form:

```text
Sol/Luna Installation Recovery Approval
Blockers: <exact reason codes>
Commands: <exact commands>
Sources: <official sources>
Scope: current user / system
Administrator elevation: YES / NO
Persistent changes: <exact changes or NONE>
Rollback: <exact uninstall or rollback route>
```

Ask for one explicit approval covering only the displayed commands. The initial
request to install Sol/Luna is not approval for these system changes. If the
user approves, run only the displayed commands, then refresh the current task
environment when possible and repeat the complete read-only prerequisite
summary. Do not automatically upgrade an already supported tool merely because
a newer version exists.

Persistent `PATH` changes require separate inclusion in the displayed proposal
and explicit approval. Never change authentication, credentials, proxy,
certificate trust, Codex sandbox, approval policy, organization policy, or
security software as a recovery action.

## 6. Guided user action

Use `NEEDS_USER_ACTION` instead of guessing when recovery depends on:

- account authentication or missing Luna model / multi-agent capability;
- an enterprise proxy, certificate, firewall, endpoint policy, or package
  allowlist;
- unavailable or unverifiable official installation guidance;
- unavailable package management, denied elevation, or declined approval;
- an unsupported operating system or Codex client;
- credentials, secrets, billing, account access, or organization policy.

Give one exact action, the check that will prove it complete, and the following
sanitized continuation block. Keep progress in the conversation; do not create
a preflight state file before `Ready: YES`.

```text
SOL_LUNA_ASSIST_RESUME
Target: v4.1.0
Phase: PREREQUISITE_RECHECK / FRESH_TASK_SMOKE
Completed checks: <names only>
Pending blocker: <one reason code>
Next proof: <one read-only command or user action>
```

After the user reports completion or pastes the block into a new task, recheck
the pending condition and its dependents instead of restarting with assumptions.

## 7. Retry budget

- Run a deterministic remediation command at most once, followed by one
  read-only recheck.
- Permit at most three total attempts for a transient GitHub HTTPS check, with
  bounded backoff.
- Never repeat a failed package-manager or elevation command automatically.
- If the same normalized reason code returns after its allowed remediation,
  stop as `NEEDS_USER_ACTION`.
- Never invent a new remediation, widen scope, or request broader permission
  merely to continue retrying.

No output for 30 seconds is not by itself a product failure. Respect the
documented command timeout and allow a command that is still running to finish,
while keeping the user informed during long work.

## 8. Handoff to the Stable setup contract

Only after the prerequisite summary reports `Ready: YES`:

1. read the pinned Stable setup contract in full;
2. execute it exactly against Stable runtime source commit
   `67a72f8accc5d53ef04ff8d64d8838e397ceecda`;
3. preserve its capability, immutable-source, ownership, dry-run, transaction,
   backup, apply, validation, and fresh-task gates.

Once setup execution starts, this assistance contract does not authorize ad hoc
repair of installer-owned files or configuration. Any setup result containing
`BLOCKED`, `FAIL`, `REVIEW REQUIRED`, an ownership or source conflict,
incomplete evidence, or an unapproved timeout must stop without manual patching
or automatic retry. Follow only an explicitly documented, installer-owned
recovery path.

## 9. Fresh-task validation and final report

An already-open task is not evidence that newly installed Global instructions
or agent configuration loaded. After installation, tell the user exactly how to
reload the current Codex client, then provide the continuation block with
`Phase: FRESH_TASK_SMOKE` for a new task.

Run the compatibility smoke from the verified immutable checkout with the
resolved Python and `CODEX_HOME`:

```text
<PYTHON> scripts/compatibility_smoke.py --codex-home <CODEX_HOME>
```

Give the command sufficient time to finish. Installation is complete only when
CLI, Luna capability, Selector, Delegation, Protected state, Runtime contract,
and final Compatibility are all explicitly `PASS`. Do not repair a smoke
failure by changing authentication, permissions, policy, ownership, or the
pinned runtime source.

The final report must state:

- target release and exact runtime source commit;
- result: `COMPLETE`, `NEEDS_USER_ACTION`, or `BLOCKED`;
- automatically recovered conditions;
- user-approved system changes;
- installer result and exact transaction backup path when one was created;
- preserved unrelated configuration;
- reload / new-task requirement;
- fresh-task smoke result or the single remaining next action.

## 10. Security floor

Never use `--dangerously-bypass-approvals-and-sandbox` or instruct the user to
widen the active sandbox to `danger-full-access` merely to make installation
succeed. Do not expose credentials, private configuration, environment dumps,
personal paths, or unrelated file content in reports. The installer remains the
sole authority for owned-file merge, backup, rollback, migration, and uninstall
behavior.
