# Codex Sol + Luna Worker

[简体中文](README.zh-CN.md)

[![Validation](https://github.com/SuperDaddyV/codex-sol-luna-worker/actions/workflows/validate.yml/badge.svg?branch=master)](https://github.com/SuperDaddyV/codex-sol-luna-worker/actions/workflows/validate.yml)
[![Stable: v4.1.2](https://img.shields.io/badge/stable-v4.1.2-blue)](https://github.com/SuperDaddyV/codex-sol-luna-worker/releases/tag/v4.1.2)
[![Historical Preview: v4.1.0-rc6](https://img.shields.io/badge/historical_preview-v4.1.0--rc6-orange)](https://github.com/SuperDaddyV/codex-sol-luna-worker/releases/tag/v4.1.0-rc6)
[![License](https://img.shields.io/github/license/SuperDaddyV/codex-sol-luna-worker)](LICENSE)

Keep GPT-5.6 Sol focused on planning, orchestration, ambiguity resolution, and final acceptance while native GPT-5.6 Luna workers handle clear, bounded execution tasks.

> [!IMPORTANT]
> This is an independent community project. It is not affiliated with, sponsored by, or endorsed by OpenAI or ModelDial.

> [!NOTE]
> `v4.1.2` is the current Stable release and default installation target. `v4.1.1` is the previous immutable Stable release, and `v4.1.0-rc6` remains an immutable historical GitHub Prerelease / Preview / Public Beta.
>
> Stable Source Commit A `551520c2435aca94d60132f292edbd53cc975cbe` passed `357` local tests and exact-SHA CI on Windows, Ubuntu, and macOS. The recorded real Global transition from `v4.1.0-rc6` changed only the selector and install manifest. After explicit Daily selection initialization, an independent one-run fresh-task compatibility smoke exited `0` after about 169.4 seconds with CLI, Luna capability, Selector, Delegation, Protected state, Runtime contract, and final Compatibility all `PASS`. RC6's recorded real Global upgrade, fresh-task O1–O10 acceptance, Final O4/O9 re-certification, and Runtime Cases A/B/C/D remain bounded evidence from one native Windows Codex environment, not universal runtime certification.
>
> The immutable Stable Assisted Installation document is anchored at `a130c676fa5924e44034dc8c27f3dc0abfc3bcad`; its underlying Stable Setup document is anchored at `4b2a6004fb92b6661166cb73e656cc2888b0a2ef`, and installer Source Commit A remains separately fixed at `551520c2435aca94d60132f292edbd53cc975cbe`. RC6 and RC5 are historical Previews.
>
> RC3 could incorrectly report `Luna unavailable` with no selector, no delegation, and no availability evidence. RC4's evidence-gated Receipt behavior remains historical release evidence. See [RUNTIME_TESTS.md](RUNTIME_TESTS.md) for the detailed record.

```text
GPT-5.6 Sol
      ↓
AGENTS delegation policy
      ↓
Daily Selector
      ↓
Native Luna / daily selected effort
      ↓
Native leaf execution
      ↓
Sol Acceptance Gate
      ↓
Delegation Receipt
```

No Hook Router is required. The selector chooses one of five Luna effort profiles once per Beijing calendar day, and same-day tasks reuse that choice. Ready to try it? Start with [Install with Codex](#install-with-codex).

## Install with Codex

1. Start a new Codex task with GPT-5.6 Sol.
2. Review the [assisted installation contract](https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/a130c676fa5924e44034dc8c27f3dc0abfc3bcad/CODEX_SOL_LUNA_INSTALL_ASSIST.md) and its pinned [setup contract](https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/4b2a6004fb92b6661166cb73e656cc2888b0a2ef/CODEX_SOL_LUNA_SETUP.md). A [review-only Chinese translation](CODEX_SOL_LUNA_INSTALL_ASSIST.zh-CN.md) is available, but the pinned English contract remains the sole executable authority.
3. Paste the prompt below.
4. Let Codex diagnose all prerequisites, apply bounded safe recovery, request approval for any system change, then run the installer's dry-run, transaction backup, installation, and validation.
5. Reload Codex when appropriate, start a new task, and run the smoke test. An already-open task is not a complete validation of newly loaded global configuration.

```text
Read and strictly execute the assisted installation contract at:

https://raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/a130c676fa5924e44034dc8c27f3dc0abfc3bcad/CODEX_SOL_LUNA_INSTALL_ASSIST.md

Install the pinned v4.1.2 Stable target. Diagnose all independent prerequisites
in one pass. Apply only the contract's safe automatic recovery. Before any
package install, administrator elevation, or persistent environment change,
show one exact official-source recovery proposal and wait for my explicit
approval. After an approved recovery, recheck and continue automatically.
Never change authentication, proxy, certificate trust, sandbox, organization
policy, or unrelated user configuration. Once Ready: YES, follow the pinned
setup contract and installer exactly. After installation, tell me how to reload
Codex and provide the fresh-task smoke continuation.
```

> [!WARNING]
> The default path uses the immutable `v4.1.2` Stable Assisted Installation contract, which wraps the separately pinned Stable Setup contract. Never substitute mutable `master`. Safe session-only recovery is bounded; system changes require explicit approval. The installer still fails closed on ownership conflicts and creates a transaction backup before changes, but no installation is risk-free.

## Current Stable

`v4.1.2` is the current Stable release and default installation target/path through the immutable assisted Stable entry above.

> [!NOTE]
> `v4.1.1` remains the previous immutable Stable release, and `v4.1.0` remains an older immutable Stable. Their tags and Releases remain unchanged, while `v4.1.0-rc6` remains the immutable historical Prerelease.

Stable contains:

- Observability metadata
- Sol/Luna Status
- Diagnostic report
- Degraded indicators
- Luna ref-cost Receipt
- Upgrade-to-latest UX
- Least-privilege child-process environments
- Installer filesystem-alias hardening
- Strict same-day Profile and selector-status validation

| Release evidence | Status |
| --- | --- |
| Installer runtime Source Commit A `551520c2435aca94d60132f292edbd53cc975cbe` | `357` tests and exact-SHA CI run `32717295801` passed on Windows, Ubuntu, and macOS |
| Immutable Stable assisted installation document | Documentation Commit `a130c676fa5924e44034dc8c27f3dc0abfc3bcad`; adds bounded prerequisite recovery without changing the runtime payload |
| Immutable Stable setup document | Documentation Commit `4b2a6004fb92b6661166cb73e656cc2888b0a2ef`; this anchor is not the runtime source |
| `v4.1.0-rc6`→`v4.1.2` recorded Global transition | `PASS`; only selector and `sol-luna-v4/install-manifest.json` changed, with one transaction backup |
| Independent one-run fresh-task compatibility smoke | Exit `0` after about 169.4 seconds; CLI, Luna capability, Selector, Delegation, Protected state, Runtime contract, and final Compatibility all `PASS` |
| Publication | `STABLE — non-draft, non-prerelease GitHub Release` |
| Real RC5→RC6 Global upgrade | `PASS` in one recorded native Windows Codex environment |
| RC6 O1–O10 and Runtime Cases A/B/C/D | `PASS` in the documented environment; bounded evidence |
| RC6 Final O4/O9 re-certification | `PASS` through the isolated acceptance harness |
| Product-runtime regression | No confirmed product-runtime regression |

The immutable assisted installation contract is the default entry above. It supports Codex Desktop on Windows, Ubuntu/Linux, or macOS, with WSL treated as a separate Linux environment. It reports all independent prerequisite failures together, automatically resolves only safe session-local conditions, and asks once before any proposed system change. The hard prerequisites remain an executable `codex` command, Python 3.11+ with `tomllib`, Git, and read-only GitHub HTTPS access. Git and the CLI are required; Codex Desktop alone is not sufficient when `codex --version` cannot run.

```text
Read and strictly execute the assisted installation contract at:

https://raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/a130c676fa5924e44034dc8c27f3dc0abfc3bcad/CODEX_SOL_LUNA_INSTALL_ASSIST.md

Complete the pinned v4.1.2 Stable installation. Aggregate all independent
read-only prerequisite results before recovery. Apply bounded safe recovery
automatically. For a required package, elevation, or persistent environment
change, present the exact commands, official sources, scope, persistent effects,
and rollback route; wait for one explicit approval, then recheck and resume.
Keep authentication, proxy, certificate trust, sandbox, policy, exact-SHA,
ownership, transaction, and fresh-task gates unchanged.
```

Review the contract first, begin with its dry-run, let the installer create its transaction backup, and preserve the exact backup path for rollback. The recorded RC6→v4.1.2 transition changes only the installed selector and manifest; policy, five agents, configuration, Daily Profile, and LKG remain preserved. RC6 O1–O10 and Final O4/O9 remain environment- and scenario-bounded evidence. No confirmed product-runtime regression.

## RC6 Historical Preview

`v4.1.0-rc6` remains available as an immutable historical GitHub Prerelease / Preview / Public Beta. Its runtime Source Commit is `50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49`, and its immutable setup document remains at documentation Commit `3e19e2f547c6fca2a888a176767e8dc69240acbc`. Its annotated tag and Release remain unchanged; do not use the historical RC6 entry as the current default.

RC6's recorded real Global upgrade, O1–O10, Final O4/O9 re-certification, and Runtime Cases A/B/C/D remain bounded historical evidence from one native Windows Codex environment. The recorded v4.1.2 transition changes the installed selector and manifest while preserving policy, five agents, configuration, Daily Profile, and LKG.

## RC5 Historical Preview

`v4.1.0-rc5` was the previous published Preview / Public Beta and is now historical. Its runtime Source Commit was `5ae88ff9190b31174c55a6136c0c8c8611d0b34c`, and its immutable setup document remains available at documentation Commit `ccd9d84da2f74df9ca2d919729b75eebf2dac27a`. Do not use that historical entry as the current default.

The documented-environment RC5 O1–O10 record remains bounded historical evidence. Its Final O4/O9 re-certification was not obtained due to `CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`; no confirmed product-runtime regression was reported. RC6 independently completed its own runtime acceptance before publication.

The RC6 installer transition changes only `sol-luna-v4/selector.py` and `sol-luna-v4/install-manifest.json`. The selector normalizes malformed URL parsing, hostname, and port `ValueError` cases to `SnapshotInvalid`, preserving the API → snapshot → LKG → fail-closed source order. The compatibility smoke adds a read-only baseline with dual exact rollout roots and bounded writer-settle/fail-closed evidence; it does not replace runtime acceptance.

## What this does

Sol remains the only planner, architect, orchestrator, ambiguity resolver, and final reviewer. It decides whether a task is suitable for delegation. Luna handles bounded implementation, targeted search, file inspection, tests, lint/build, repetitive work, and clearly scoped batch tasks. Luna returns evidence; Sol accepts or rejects the result.

The design keeps high-value reasoning and acceptance with Sol without spending Sol effort on every mechanical step. It does not promise a fixed cost or speed improvement.

## What it installs

| Component | Global destination | Purpose |
| --- | --- | --- |
| Five Luna roles | `<CODEX_HOME>/agents/luna-{low,medium,high,xhigh,max}.toml` | Native GPT-5.6 Luna workers at five stable efforts |
| Global policy | Managed block in `<CODEX_HOME>/AGENTS.md` | Sol/Luna delegation, Task Contract, Context Firewall, acceptance, and Delegation Receipt policy |
| Multi-agent settings | Managed block in `<CODEX_HOME>/config.toml` | Enables multi-agent work and caps direct children at 3 |
| Daily Selector | `<CODEX_HOME>/sol-luna-v4/selector.py` | Resolves the Beijing-day Luna role |
| Selector state | `<CODEX_HOME>/sol-luna-v4/state/` | Daily profile, last-known-good record, and lock, created on first use |
| Install manifest | `<CODEX_HOME>/sol-luna-v4/install-manifest.json` | Records installer ownership for upgrades, rollback safety, and uninstall |

The repository-local `.var/` directory may be used by selector development commands, but it is non-authoritative development state rather than an authority for actual Codex project delegation. Actual project delegation follows the inherited Global installed-selector policy.

All five Luna roles use `model = "gpt-5.6-luna"`; their efforts are `low`, `medium`, `high`, `xhigh`, and `max`. Every role is a native leaf with `[agents] enabled = false`, so a Luna child cannot create another agent. `ultra` is deliberately excluded.

The v4 core does **not** install a Hook Router, `PreToolUse` enforcement, a managed-child registry, daemon, database, scheduler, dashboard, plugin framework, or custom orchestration engine.

## Core features

- Sol is the sole brain and final acceptance owner.
- Automatic delegation follows the effective `AGENTS.md` policy and the installed Global selector's current Beijing-day role; the user normally does not name a Luna role.
- Five stable native Luna roles cover `low` through `max`; `ultra` never enters the selector allowlist.
- The selector runs once per Beijing day, reuses the same-day profile, can fall back to a valid last-known-good snapshot, and fails closed when first use has no valid source or fallback.
- A supplied local capability set can degrade an unavailable source winner to the best supported effort.
- Luna is a native leaf. Sol may run at most three direct Luna children concurrently, and only for independent work.
- Every delegation carries a bounded Task Contract and a minimal Context Firewall.
- A final one-line Delegation Receipt summarizes the already-observed delegated or Sol-only outcome for non-trivial work. `Luna unavailable` requires current-task parent-visible availability failure evidence and is never the default Sol-only fallback. Receipt generation does not alter the delegation threshold or create evidence by invoking a selector, probe, tool, child, network, state, telemetry, or repository write.
- The installer uses explicit targets, managed ownership, atomic writes, transaction backups, exact rollback, safe uninstall, and exact-schema legacy `3.2` migration.
- Global installation and project-scoped custom agents are both supported by Codex's native configuration layers.

## Requirements and compatibility

- Codex Desktop for the copy-and-paste installation workflow.
- A current Codex client with custom agents and multi-agent/subagent support.
- A `codex` command already resolvable in the task environment; Codex Desktop alone is not sufficient when `codex --version` cannot run.
- Access to GPT-5.6 Sol for the primary task and GPT-5.6 Luna at all required efforts for workers.
- Python 3.11 or newer with the standard-library `tomllib` module.
- Git for the required immutable exact-commit checkout; the setup contract has no archive or downloader fallback.
- Read-only HTTPS access to the public GitHub repository. `curl` is not required.
- Windows, Ubuntu/Linux, or macOS. WSL is a separate Linux environment and must not share assumptions or paths with native Windows.

RC5 repository validation and exact-SHA CI passed on Windows, Ubuntu, and macOS. The documented-environment RC5 O1–O10 record remains bounded evidence, including O4 and O9; Final O4/O9 re-certification was not obtained due to `CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`. No confirmed product-runtime regression. Earlier published RC1, RC2, RC3, and RC4 runtime records remain historical evidence, including RC2's `FRESH_REPO_CONTEXT_DELEGATION_PASS`. CI PASS does not imply that real Codex runtime validation was performed on every operating system, account, client, or user.

Official Codex behavior is documented in [AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents), and the [Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference). OpenAI lists the model IDs in its [model catalog](https://developers.openai.com/api/docs/models).

## Daily use

Use Codex normally. You do not need to choose `luna_low`, `luna_max`, or any other role in routine prompts. Sol decides whether work is bounded enough to delegate; not every prompt will create a child.

### Coding

```text
Review this project, fix the failing tests, and verify the result.
```

### Inspection

```text
Check these modules for inconsistent configuration and summarize the findings.
```

### Independent work

```text
Review the frontend, backend, and tests independently, then give me one final assessment.
```

The last example invites parallel work, but Sol still decides whether the parts are independent and safe to delegate. After installation or an update, begin daily use in a new task so Codex reloads global instructions, agents, and configuration.

## How do I know Sol + Luna is working?

For a non-trivial task, the final line reports one observed outcome. A delegated task uses `Sol/Luna: delegated · <role> ×<direct_child_count>` and adds ` · parallel` only when at least two direct Luna children actually overlapped. A Sol-only task reports one high-level reason such as `task too small`, `reasoning/architecture task`, `no independent bounded work`, or `Luna unavailable`. The last category is valid only after the current task's normal execution path already produced parent-visible selector or native-agent availability failure evidence; no delegation by itself is not evidence of unavailability.

`0 Luna` does not mean installation failure. Sol should keep trivial, reasoning-heavy, ambiguous, or tightly coupled work. The Receipt is a low-noise execution summary, not runtime attestation; verify actual child metadata when formal runtime proof matters.

## Feedback

`v4.1.2` is the current Stable release. `v4.1.1` is the previous immutable Stable release, and `v4.1.0-rc6` remains a historical Preview prerelease and public beta.

Use the matching native GitHub Issue Form for install, upgrade, selector, Luna delegation, Delegation Receipt, rollback, or uninstall issues. Successful compatibility reports are welcome too:

- [Bug Report](https://github.com/SuperDaddyV/codex-sol-luna-worker/issues/new?template=bug-report.yml)
- [Compatibility Report, including a successful run](https://github.com/SuperDaddyV/codex-sol-luna-worker/issues/new?template=compatibility-report.yml)
- [Feature / Feedback](https://github.com/SuperDaddyV/codex-sol-luna-worker/issues/new?template=feature-feedback.yml)

> [!WARNING]
> Before submitting, remove or redact secrets and private information, including API keys, access tokens, cookies, passwords, private repository credentials, personal email addresses, unnecessary absolute home-directory information, and proprietary source/code unless intentionally shared. Include only the minimum relevant logs. Do not upload the entire CODEX_HOME (the whole `CODEX_HOME`) unless specifically requested during later troubleshooting. `CODEX_HOME` is a private user configuration root.

### Codex Compatibility Smoke

After a Codex Desktop or CLI update, start a fresh task and ask `检查 Sol/Luna 与当前 Codex 是否兼容`, or run the lightweight smoke directly:

```text
python scripts/compatibility_smoke.py --codex-home "<CODEX_HOME>"
```

The smoke is read-only for the repository and managed selector state. Its ephemeral capability checks and one-child delegation create normal Codex session/runtime records and can make up to six model calls; its before/after snapshots cannot attest fully transient activity.

`PASS` means only that basic Sol/Luna use is compatible with the current observed Codex environment; no project change or further review is required. `REVIEW REQUIRED` means run only the recommended targeted compatibility review. `BLOCKED` means the CLI prerequisite could not run. Reported runtime paths are irreversible fingerprints rather than private relative paths. This smoke does not replace O1–O10 acceptance, cross-platform certification, Stable certification, or a future-version guarantee.

### Basic read-only self-test

Run this in a fresh task after installation or upgrade. It naturally offers bounded inspection work but does not require a child:

```text
Read README.md and README.zh-CN.md without modifying files. Compare their installation-status and validation-boundary statements, then report any inconsistency. Follow the current delegation policy normally; do not name a role, model, or effort. Sol must independently review the result and include the normal final Delegation Receipt.
```

## Daily Luna selection

The selector validates a complete five-effort publication, chooses the highest score, and breaks ties toward the lower effort. When given a restricted supported-effort set, it selects the best supported alternative and marks capability degradation. It locks the result to the Beijing calendar day and reuses it for that day.

The v4.1 source order is the official [ModelDial API v1](https://modeldial.com/api/v1/radar/latest.json), then the official [full snapshot JSON](https://modeldial.com/data/reference-snapshots/latest.json), then a valid last-known-good record. A valid API response stops acquisition immediately. Radar HTML runtime fallback is removed in v4.1. On first use, no valid source plus no valid fallback returns `NO_LUNA_PROFILE_AVAILABLE`; Sol keeps the task instead of guessing an effort. The installer itself does not contact ModelDial, and it never converts a legacy daily profile.

## Safety and configuration protection

- Mutating installer modes require an explicit `--codex-home`.
- Existing `config.toml` and `AGENTS.md` content is preserved outside project-owned marker blocks.
- A non-empty `AGENTS.override.md`, a same-name unowned agent, a changed owned file, malformed TOML, or unsupported manifest fails closed.
- Every effective install or upgrade creates and verifies a centralized backup before writing the v4 manifest last.
- Migration accepts only the exact legacy schema `3.2`, removes only manifest-owned legacy content, and preserves unowned audit evidence.
- Publishing or updating this repository never installs into a user's Codex home automatically.
- Native leaf configuration removes multi-agent tools from Luna children; it is a workflow boundary, not a server-side or cryptographic security boundary.

See [SECURITY.md](SECURITY.md) for the complete boundary.

## Rollback and uninstall

Use the exact backup path returned by a successful install or upgrade:

```powershell
python scripts/install.py --rollback "<BACKUP_PATH>" --codex-home "<CODEX_HOME>"
```

Rollback verifies the installer-owned snapshot, restores the exact pre-install state, and consumes that backup after success. Uninstall is also manifest-owned and fails closed if installed content was changed:

```powershell
python scripts/install.py --uninstall --codex-home "<CODEX_HOME>"
```

Uninstall removes only v4-owned files and blocks while preserving unrelated user content. Reload Codex and start a new task after either operation. See the [setup contract](https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/4b2a6004fb92b6661166cb73e656cc2888b0a2ef/CODEX_SOL_LUNA_SETUP.md) before acting.

## Validation status

| Validation | Status |
| --- | --- |
| Native custom Luna | `PASS` |
| Automatic AGENTS delegation | `PASS` |
| Native leaf | `PASS` |
| Native parallel | `PASS` |
| Sol Acceptance | `PASS` |
| Clean installer | `PASS` |
| Legacy migration simulation | `PASS` |
| Stable runtime Source Commit exact-SHA CI | Passed on Windows, Ubuntu, and macOS |
| Stable immutable assisted installation document | Documentation Commit `a130c676fa5924e44034dc8c27f3dc0abfc3bcad`; current default entry, not runtime source |
| Stable immutable setup document | Documentation Commit `4b2a6004fb92b6661166cb73e656cc2888b0a2ef`; pinned by the assisted contract, not runtime source |
| `v4.1.0-rc6`→`v4.1.2` recorded Global transition | Installer apply PASS; selector and manifest only, with one transaction backup |
| Stable compatibility smoke | One run, exit `0`, seven checks and final Compatibility `PASS` |
| RC5 repository validation and exact-SHA CI | Passed on Windows, Ubuntu, and macOS |
| RC5 O1–O10 documented-environment record, including O4/O9 | Bounded evidence only |
| RC5 Final O4/O9 re-certification | Not obtained due to `CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY` |
| RC5 product-runtime regression | No confirmed product-runtime regression |
| RC6 runtime Source Commit exact-SHA CI | Passed on Windows, Ubuntu, and macOS |
| RC6 immutable setup document | Historical documentation Commit `3e19e2f547c6fca2a888a176767e8dc69240acbc`; not the current default |
| RC6 RC5→RC6 fake-home lifecycle | Local installer/lifecycle tests PASS; selector and manifest only |
| RC6 real Global upgrade and O1–O10 | `PASS` in the documented environment; bounded evidence |
| RC6 Final O4/O9 re-certification | `PASS` through the isolated acceptance harness |
| RC6 product-runtime regression | No confirmed product-runtime regression |
| RC4 source suite | `PASS` |
| RC4 real Global upgrade | `PASS` |
| RC4 Case A | `PASS` |
| RC4 Case B | `PASS` |
| RC4 Case C | `PASS` |
| RC4 controlled Case D | `PASS` |
| RC3 real Global upgrade | `PASS` |
| RC3 Sol-only Receipt | `PASS` |
| RC3 delegated Receipt | `PASS` |
| Windows CI | `PASS` |
| Ubuntu CI | `PASS` |
| macOS CI | `PASS` |

The published RC4 prerelease passed its recorded real RC3→RC4 Global upgrade with two effective changes, second-apply idempotency, and rollback readiness. Case A verified the Sol reasoning Receipt; Case B verified three direct `luna_max` children, native leaf behavior, parallel overlap, zero grandchildren, and Sol acceptance; Case C directly regressed the no-selector, no-delegation, no-evidence misclassification; controlled Case D allowed `Luna unavailable` only with genuine availability evidence and forbade it without evidence. RC3 remains historical prerelease evidence. These results apply only to the recorded environments in which they were observed. CI PASS does not imply real Codex runtime validation on every operating system, account, client, or user. Detailed evidence boundaries are in [RUNTIME_TESTS.md](RUNTIME_TESTS.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

## FAQ

### Why not let Sol do every task?

Sol can do everything itself, and it keeps trivial or ambiguous work. This policy reserves Sol's attention for requirements, decisions, orchestration, and acceptance when execution can be safely bounded.

### Why not send every task to Luna?

Luna is intentionally an execution worker. Architecture decisions, unresolved ambiguity, scope expansion, and final acceptance stay with Sol.

### Do I select the Luna effort manually?

Normally, no. The Daily Selector returns one stable role for the Beijing day, and Sol uses it only when delegation is worthwhile.

### What if ModelDial is unavailable?

The same-day profile is reused. A new-day selection tries the official API, then the official full snapshot, then a valid last-known-good record. First use without a valid source or fallback fails closed, and Sol performs the work without guessing a Luna effort.

### Why is `ultra` excluded?

The frozen v4 policy defines five tested Luna roles from `low` through `max`. `ultra` is outside that stable selection and validation contract.

### Can Luna create more agents?

No. Every formal Luna role sets `[agents] enabled = false` and is a native leaf.

### Will an already-open Codex task use the new installation?

Do not rely on it. Codex builds its instruction chain when a run or task starts. Reload Codex Desktop/App Server when appropriate and start a new task for full validation.

### What happens to a project's own `.codex/agents`?

Global agents provide personal defaults; project-scoped agents and project `AGENTS.md` can coexist in the project context. Inspect the effective project configuration instead of assuming global files replace project-owned definitions or instructions.

### Does v4 require Hooks?

No. v4 uses native custom agents and `AGENTS.md` policy. Legacy Hook files may exist as historical evidence, but they are not a current runtime requirement.

### Can I roll back or uninstall?

Yes, when the v4 manifest and relevant backup are intact. Use the installer's real `--rollback` and `--uninstall` modes; do not hand-edit TOML to simulate either operation.

## Advanced / manual inspection

The Codex-driven path is recommended. For a human review, acquire an immutable commit, inspect the contract and source, and run only the read-only checks first:

```powershell
git clone https://github.com/SuperDaddyV/codex-sol-luna-worker.git
cd codex-sol-luna-worker
git checkout --detach <APPROVED_40_HEX_COMMIT>
python scripts/install.py --help
python scripts/install.py --dry-run --codex-home "<CODEX_HOME>"
python -m unittest discover -s tests -v
```

Do not use `--validation-sandbox` for a real global installation; that flag exists only for repository-local test targets. Apply, migration, rollback, and uninstall commands are specified in [CODEX_SOL_LUNA_SETUP.md](https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/4b2a6004fb92b6661166cb73e656cc2888b0a2ef/CODEX_SOL_LUNA_SETUP.md).

### Optional parallel self-test

In a fresh task, request two or three independent bounded read-only checks and ask Sol for one reviewed conclusion. Do not require spawning or name a role. Accept ` · parallel` only when at least two direct Luna children actually overlapped according to parent-visible runtime evidence; the Receipt text alone is not proof.

## Technical documentation

- [Codex-executable assisted installation contract](https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/a130c676fa5924e44034dc8c27f3dc0abfc3bcad/CODEX_SOL_LUNA_INSTALL_ASSIST.md)
- [Review-only Chinese translation of the assisted installation contract](CODEX_SOL_LUNA_INSTALL_ASSIST.zh-CN.md)
- [Codex-executable setup contract](https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/4b2a6004fb92b6661166cb73e656cc2888b0a2ef/CODEX_SOL_LUNA_SETUP.md)
- [Architecture](ARCHITECTURE.md)
- [Runtime validation](RUNTIME_TESTS.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)
- [MIT License](LICENSE)

## License

[MIT](LICENSE)

ModelDial-derived test data under `fixtures/modeldial/` is attributed separately in [its fixture notice](fixtures/modeldial/README.md) under CC BY 4.0; this does not change the source-code license.
