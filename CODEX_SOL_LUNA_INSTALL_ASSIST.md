# Sol/Luna v4.1.1 Assisted Installation Contract

Assistance contract version: `2`.

The English contract is the only executable authority. The review-only Chinese
translation is `CODEX_SOL_LUNA_INSTALL_ASSIST.zh-CN.md`; it must identify this
English contract and must not become a second executable installation source.

This document is the user-facing recovery wrapper for the reviewed `v4.1.1`
Stable installation. It improves prerequisite diagnosis and bounded recovery;
it does not change the Stable runtime payload or installer and does not itself
create, move, or rewrite a tag or Release.

## 1. Immutable target

Use only these reviewed identities:

- Stable release: `v4.1.1`;
- Stable runtime Source Commit A2:
  `ca8e9e4caf5564ffe8d0a11fe376047594f8a748`;
- Stable setup contract documentation commit:
  `d4a044a04df509285ef38c6afc28b5a68a48a0f9`;
- Stable setup contract:
  `https://raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/d4a044a04df509285ef38c6afc28b5a68a48a0f9/CODEX_SOL_LUNA_SETUP.md`.

Never substitute mutable `master`, another branch, `target_commitish`, an
archive, or a different Release. `v4.1.0` remains the previous immutable Stable
release. `v4.1.0-rc6` remains an immutable historical Prerelease / Preview /
Public Beta. Do not move or rewrite any tag or Release.

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
Target: v4.1.1
Runtime source: ca8e9e4caf5564ffe8d0a11fe376047594f8a748
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
Target: v4.1.1
Phase: PREREQUISITE_RECHECK / SELECTOR_INITIALIZATION / FRESH_TASK_SMOKE
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
   `ca8e9e4caf5564ffe8d0a11fe376047594f8a748`;
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
reload the current Codex client. Continue first with
`Phase: SELECTOR_INITIALIZATION` and run:

```text
<PYTHON> <CODEX_HOME>/sol-luna-v4/selector.py --state-dir <CODEX_HOME>/sol-luna-v4/state --ensure-daily --print-selection
```

Require exit code `0`, an allowed `selected_role` (`luna_low`, `luna_medium`,
`luna_high`, `luna_xhigh`, or `luna_max`), and a matching `selected_effort`.
Only after that proof may the continuation advance to
`Phase: FRESH_TASK_SMOKE` in another new task. The smoke is deliberately
read-only for managed selector state; it must not initialize Daily selection or
add `--ensure-daily` to its own status check.

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

## 11. v4.1.1 deterministic Stable assistance

This section specifies the deterministic installation experience for the
reviewed `v4.1.1` Stable target. It is subordinate to the exact setup contract
and Source Commit A2 above and is not authority to publish, retag, or move a
Release. The bilingual README must pin this English contract through a separate
exact immutable documentation commit; that commit is not the runtime source.

### 11.1 Bootstrap boundary

P3 standalone bootstrap is explicitly out of scope. The deterministic Python
assistant cannot run when Python is absent, and a repository script cannot run
before Git and immutable source acquisition are available. Until Python 3.11+
and Git are usable, Codex follows Sections 3–7 in the conversation and requests
approval for every package, elevation, or persistent environment change.

After Python, Git, and immutable source acquisition succeed, use
`scripts/install_assist.py`. The assistant must never claim that it repairs a
machine with no usable Python by itself.

### 11.2 Deterministic command and state contract

The assistant exposes these commands:

```text
<PYTHON> scripts/install_assist.py check --codex-home <CODEX_HOME>
<PYTHON> scripts/install_assist.py plan --codex-home <CODEX_HOME>
<PYTHON> scripts/install_assist.py recover --codex-home <CODEX_HOME> --approve <PLAN_ID>
<PYTHON> scripts/install_assist.py install --codex-home <CODEX_HOME> --source-commit ca8e9e4caf5564ffe8d0a11fe376047594f8a748
<PYTHON> scripts/install_assist.py install --apply --codex-home <CODEX_HOME> --source-commit ca8e9e4caf5564ffe8d0a11fe376047594f8a748
<PYTHON> scripts/install_assist.py report --codex-home <CODEX_HOME> --format json
```

Every result is structured JSON and contains exactly one current phase from:

```text
CHECKING
SAFE_RECOVERY
AWAITING_APPROVAL
RECHECKING
CAPABILITY_PRECHECK
DRY_RUN
INSTALLING
RELOAD_REQUIRED
SELECTOR_INITIALIZATION
FRESH_TASK_SMOKE
COMPLETE
NEEDS_USER_ACTION
BLOCKED
```

No preflight state file is created. `recover` recomputes the live read-only
snapshot and exact recovery plan, then requires the displayed SHA-256-derived
`PLAN_ID`. A changed command, source, scope, impact, proof, rollback route, or
blocker changes the ID and fails closed as `RECOVERY_PLAN_CHANGED`. A
deterministic recovery action runs at most once and receives one proof check;
the assistant never repeats a failed package-manager or elevation command.

### 11.3 Environment and permission summary

All commands report a bounded summary containing operating-system family, WSL
classification, approval policy, sandbox mode, administrator requirement,
Codex/Python/Git versions, GitHub HTTPS status, and installed Sol/Luna version.
Approval policy and sandbox mode are caller-supplied display context; the
assistant does not parse or dump user configuration and never grants itself
permission.

### 11.4 Recovery catalog

`scripts/install_recovery_catalog.json` is the only command catalog. Each entry
contains a stable action ID, normalized blocker, platform and package manager,
classification (`approval_required` or `user_action`), exact argument vector,
official source, scope, administrator and persistent-change impact, proof, and
rollback. The implementation accepts only HTTPS sources on its fixed official
domain allowlist and never executes shell strings, pipelines, redirects,
command substitution, or an action missing proof or rollback metadata.
`user_action` entries use an empty argument vector and a bounded instruction;
only `approval_required` entries are executable.

The initial catalog covers WinGet on Windows, Homebrew on macOS, and APT on
Ubuntu/Debian. Unsupported distributions, absent package managers, Codex
authentication, proxy/certificate/firewall policy, and unavailable verified
guidance return `NEEDS_USER_ACTION`. Codex CLI installation remains guided user
action because its official installation and sign-in path can require an
additional runtime or interactive authentication.

### 11.5 Installed-version fast path

Before capability calls or installer execution, classify the ownership
manifest metadata as absent, current, older, newer, or invalid. After capability
PASS, the installer dry-run is the sole byte-consistency and ownership check. A
current installation whose dry-run returns `IDEMPOTENT_PASS` performs zero
writes and zero backups, but it still requires immutable-source verification
and explicit Daily selection proof plus a later fresh-task smoke before
`COMPLETE`. A newer version fails closed as
`CURRENT_VERSION_NEWER`. Invalid or ownership-conflicting state is `BLOCKED`;
it is never repaired by editing managed files outside `scripts/install.py`.

### 11.6 Early capability and installer handoff

After hard prerequisites and immutable checkout verification, but before any
real `CODEX_HOME` dry-run or write, run the five Luna efforts through ephemeral
Codex executions with user config ignored and sandbox `read-only`. Do not write
probe state, copy authentication, change approval policy, or widen the sandbox.
Any unavailable effort, timeout, authentication/account limitation, or
incomplete evidence stops as `NEEDS_USER_ACTION` before installer execution.

Only `scripts/install.py` may perform ownership checks, target writes,
transaction backup, rollback, migration, or uninstall. The assistant first
calls the installer's non-mutating dry-run. `install` without `--apply` stops at
`DRY_RUN`; `install --apply` may hand off to the transactional installer only
after the caller explicitly authorizes that mode.

After apply, `RELOAD_REQUIRED` hands off to `SELECTOR_INITIALIZATION`; an
`IDEMPOTENT_PASS` fast path enters the same initialization phase without an
installer write or backup. Complete any pending Codex reload, then run exactly:

```text
<PYTHON> <CODEX_HOME>/sol-luna-v4/selector.py --state-dir <CODEX_HOME>/sol-luna-v4/state --ensure-daily --print-selection
```

This is an explicit normal selector-state operation, not an assistant repair.
Accept only exit code `0`, one allowed `selected_role`, and the corresponding
`selected_effort`. The command may create or reuse the valid Beijing-day
selection. The continuation block records
`Pending blocker: DAILY_SELECTION_PROOF_REQUIRED`. On failure or incomplete
evidence, stop without automatic retry.
On PASS, start another new task and run the one allowed compatibility smoke.
The smoke remains status-only and must never initialize the selection itself.

### 11.7 Sanitized support report

`report` is whitelist-only. It may include schema/version, phase, normalized
reason codes, platform family, WSL boolean, caller-supplied permission labels,
tool versions, package-manager name, installed project version, strictly
validated source commit, action IDs and success/failure status. It represents
the target as `<CODEX_HOME>` and omits real paths, environment variables,
configuration content, authentication, command stderr/stdout, logs, arbitrary
URLs, exception text, identifiers, and secrets.

### 11.8 Result cards

Human-facing output derived from the structured result uses exactly one card:

```text
Reload Required
Version: <version>
Source: <40HEX>
Backup: <symbolic identifier or NONE>
Next: reload Codex, then initialize the Daily selection
Resume: <sanitized SELECTOR_INITIALIZATION continuation block>
```

```text
Selector Initialization Required
Version: <version>
Reason: DAILY_SELECTION_PROOF_REQUIRED
Action: <canonical --ensure-daily --print-selection command>
Proof: <allowed selected_role and matching selected_effort>
Next: start a new task for the one-run compatibility smoke
```

```text
Installation Complete
Version: <version>
Source: <40HEX>
Repairs: <action IDs or NONE>
Approved system changes: <action IDs or NONE>
Backup: <symbolic identifier or NONE>
Configuration preserved: YES
Next: installation and fresh-task smoke are complete
```

```text
Needs User Action
Phase: <phase>
Reason: <one normalized reason code>
Action: <one bounded action>
Proof: <one read-only proof>
Resume: <sanitized SOL_LUNA_ASSIST_RESUME block>
```

```text
Blocked
Phase: <phase>
Reason: <one normalized reason code>
Writes performed: NO / ROLLED_BACK
Next: stop; do not patch managed state or retry automatically
```
