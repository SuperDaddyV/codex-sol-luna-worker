# Codex Sol + Luna Worker

Keep GPT-5.6 Sol focused on planning and acceptance while native GPT-5.6 Luna workers handle clear, bounded execution.

[简体中文](README.zh-CN.md)

[![Stable: v4.1.2](https://img.shields.io/badge/stable-v4.1.2-blue)](https://github.com/SuperDaddyV/codex-sol-luna-worker/releases/tag/v4.1.2)
[![Validation](https://github.com/SuperDaddyV/codex-sol-luna-worker/actions/workflows/validate.yml/badge.svg?branch=master)](https://github.com/SuperDaddyV/codex-sol-luna-worker/actions/workflows/validate.yml)
[![License](https://img.shields.io/github/license/SuperDaddyV/codex-sol-luna-worker)](LICENSE)

> [!IMPORTANT]
> This is an independent community project. It is not affiliated with, sponsored by, or endorsed by OpenAI or ModelDial.

## What it is

Codex Sol + Luna Worker adds a simple division of responsibility to Codex:

- **Sol plans and accepts.** Sol owns requirements, architecture, orchestration, ambiguity resolution, and the final answer.
- **Luna executes bounded work.** Luna handles clearly scoped implementation, targeted inspection, tests, builds, and repetitive tasks, then returns evidence to Sol.

Sol remains in control: it decides whether delegation is appropriate and reviews every Luna result before acceptance.

## Core value

- **Native agents:** uses Codex custom agents and subagents, without a Hook Router or custom orchestration engine.
- **Automatic Daily Luna:** selects one of five Luna effort profiles for the Beijing calendar day; routine prompts do not name a role or effort.
- **Independent-task delegation:** keeps reasoning and final decisions with Sol while moving clear execution to Luna.
- **Limited parallelism:** allows at most three direct Luna workers, only for genuinely independent tasks; Luna workers are native leaves and cannot delegate again.
- **Configuration protection and recovery:** preserves unrelated user configuration, fails closed on conflicts, and uses transaction backups for supported rollback and safe uninstall.

## Requirements

- Codex Desktop or another current Codex client with custom-agent and subagent support.
- A working `codex` command in the task environment. Codex Desktop alone is not sufficient if `codex --version` cannot run.
- Access to GPT-5.6 Sol and GPT-5.6 Luna at the required five effort levels.
- Python 3.11 or newer with `tomllib`, plus Git for the required immutable exact-commit checkout.
- Read-only HTTPS access to this public GitHub repository.
- Windows, Ubuntu/Linux, or macOS. Treat WSL as a separate Linux environment.

## Install with Codex

Start a new Codex task with GPT-5.6 Sol and paste this single prompt:

```text
Read and strictly execute the assisted installation contract at:

https://raw.githubusercontent.com/SuperDaddyV/codex-sol-luna-worker/a130c676fa5924e44034dc8c27f3dc0abfc3bcad/CODEX_SOL_LUNA_INSTALL_ASSIST.md

Install the pinned v4.1.2 Stable target. Diagnose all independent prerequisites
in one pass. Apply only the contract's safe automatic recovery. Before any
package install, administrator elevation, or persistent environment change,
show one exact official-source recovery proposal and wait for my explicit
approval. After approval, recheck and continue automatically. Never change
authentication, proxy, certificate trust, sandbox, organization policy, or
unrelated user configuration. Once Ready: YES, follow the pinned setup contract
and installer exactly. After installation, tell me how to reload Codex and
provide the fresh-task smoke continuation.
```

The immutable [English Assisted Installation contract](https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/a130c676fa5924e44034dc8c27f3dc0abfc3bcad/CODEX_SOL_LUNA_INSTALL_ASSIST.md) is the sole executable authority. The [review-only Chinese translation](CODEX_SOL_LUNA_INSTALL_ASSIST.zh-CN.md) is available for review. The assisted contract pins the separate [Setup contract](https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/4b2a6004fb92b6661166cb73e656cc2888b0a2ef/CODEX_SOL_LUNA_SETUP.md), which pins runtime Source Commit A `551520c2435aca94d60132f292edbd53cc975cbe`.

> [!WARNING]
> Never replace the immutable installation URL with `master`, a tag, or another mutable entry. System changes require explicit approval. The installer fails closed on ownership conflicts and creates a transaction backup before changes, but no installation is risk-free.

After installation, reload Codex when instructed and start a new task so the global instructions, agents, and configuration are loaded.

## Daily use

Use Codex normally. Sol decides whether a task is suitable for delegation; not every prompt should create a Luna worker.

```text
Review this project, fix the failing tests, and verify the result.
```

```text
Inspect these modules for inconsistent configuration and report the findings without changing files.
```

```text
Update the user documentation for this feature, then run the relevant checks.
```

```text
Review the frontend, backend, and tests independently, then give me one final assessment.
```

The final example gives Sol independent work that may run in parallel; Sol still owns the decision and final review.

## Confirm it is working

In a fresh Codex task, run this read-only status command:

```text
Check Sol/Luna status.
```

`Status Healthy` means the installed Sol/Luna files and managed configuration passed the health checks. `Agents 5/5 Ready` and `Native leaf Ready` mean all five Luna profiles are available and remain non-delegating workers. A healthy installation may show today's selection as not initialized until delegation is first needed.

For deeper runtime evidence after installation or a Codex update, follow [RUNTIME_TESTS.md](RUNTIME_TESTS.md); a status result alone is not full runtime acceptance.

After a Codex update, the `Codex Compatibility Smoke` in `scripts/compatibility_smoke.py` is the targeted next check: `PASS` means no project change, while `REVIEW REQUIRED` means follow only the recommended review. It does not replace the O1–O10 evidence in [RUNTIME_TESTS.md](RUNTIME_TESTS.md).

## Upgrade, rollback, and uninstall

- **Upgrade:** in a new task, ask `Upgrade Sol/Luna to the latest version`. Codex follows the installed release-discovery and immutable-source gates.
- **Rollback:** use the exact transaction backup returned by the installer. A successful rollback restores the verified pre-change state.
- **Uninstall:** use the installer's manifest-owned uninstall flow; do not hand-edit managed TOML or agent files.

Reload Codex and start a new task after an upgrade, rollback, or uninstall. Commands, stop conditions, ownership rules, and backup behavior are defined in the immutable [Setup contract](https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/4b2a6004fb92b6661166cb73e656cc2888b0a2ef/CODEX_SOL_LUNA_SETUP.md).

## Technical documentation

- [Installation, upgrade, rollback, and uninstall](https://github.com/SuperDaddyV/codex-sol-luna-worker/blob/4b2a6004fb92b6661166cb73e656cc2888b0a2ef/CODEX_SOL_LUNA_SETUP.md)
- [Architecture](ARCHITECTURE.md)
- [Runtime evidence](RUNTIME_TESTS.md)
- [Security boundaries](SECURITY.md)
- [Version history](CHANGELOG.md)
- [GitHub Releases](https://github.com/SuperDaddyV/codex-sol-luna-worker/releases)

## Feedback

- [Bug Report](https://github.com/SuperDaddyV/codex-sol-luna-worker/issues/new?template=bug-report.yml)
- [Compatibility Report](https://github.com/SuperDaddyV/codex-sol-luna-worker/issues/new?template=compatibility-report.yml)
- [Feature / Feedback](https://github.com/SuperDaddyV/codex-sol-luna-worker/issues/new?template=feature-feedback.yml)

Before submitting, remove secrets and private information, share only the minimum relevant logs, and do not upload the entire `CODEX_HOME`.

## License

[MIT](LICENSE)

ModelDial-derived test data under `fixtures/modeldial/` is attributed separately in [its fixture notice](fixtures/modeldial/README.md) under CC BY 4.0; this does not change the source-code license.
