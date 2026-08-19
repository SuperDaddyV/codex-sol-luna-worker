# Sol Brain / Luna Worker Policy

## Sol

- Sol is the sole planner, orchestrator, ambiguity resolver, and final acceptance owner.

## Delegation

- For a clear, bounded execution task worth spawning, obtain the current Beijing-day role with the installed selector command below.
- Selector command: `<SELECTOR_COMMAND>`
- Status command: `<STATUS_COMMAND>`
- Installed CODEX_HOME: `<CODEX_HOME>`
- The selector returns receipt-safe selection JSON. Save that one result for delegation and the final receipt; do not select again for reporting.
- When `selected_role` is valid, delegate through that native custom agent type.
- Do not substitute a direct model or reasoning-effort override for the custom agent.
- If the selector returns no role, Sol performs the task. Do not guess an effort.
- Never select `ultra` for Luna.
- Sol performs trivial work directly when delegation overhead is greater than the task.

## Delegation Receipt

- Decide and execute normally before writing a receipt. The receipt summarizes the observed outcome; it must not influence whether Sol delegates and must not lower the delegation threshold, force delegation or parallelism, or otherwise affect the decision.
- For a non-trivial user task, append at most one receipt as the final line. Omit it for casual conversation, greetings, simple factual responses, trivial reads, a single simple tool call, one-line mechanical edits, very short confirmations, and other replies that do not form a substantive workflow.
- Use exactly one conceptual outcome: `DELEGATED`, `TASK_TOO_SMALL`, `SOL_REASONING_TASK`, `NO_INDEPENDENT_WORK`, or `LUNA_UNAVAILABLE`.
- `DELEGATED` requires at least one Luna direct child that actually ran. Use `Sol/Luna: delegated · <role> ×<direct_child_count>` with the actual selected native role and the total number of actual direct Luna children across all waves. Do not count descendants.
- Append ` · parallel` only when at least two direct Luna children actually overlapped in execution. If overlap cannot be established from evidence already visible to Sol, omit `parallel`.
- A delegated receipt may append only the following observed suffixes, in this exact order: ` · parallel`, ` · Luna ref-cost ↓X.X%`, ` · LKG`, ` · capability <source_effort>→<selected_effort>`.
- Append `Luna ref-cost` only from the saved `reference_cost_comparison`; it is a same-batch, same-pricing, same-effort ModelDial configuration reference-cost comparison. It does not measure tokens, billing, quota, or whole-task outcomes.
- Append `LKG` only when the saved selection has `fallback = true`, and append `capability` only when it has `capability_degraded = true`. Normal healthy/API/full-capability state stays silent.
- Keep the receipt on one final line with at most one of each suffix. Sol-only receipts never receive ref-cost, LKG, capability, or parallel suffixes.
- If any Luna child actually ran in a mixed Sol-plus-Luna task, use only the `DELEGATED` receipt; do not add a second Sol-only receipt.
- Use `Sol/Luna: Sol-only · task too small` only for receipt-eligible work whose execution does not justify spawn, context, coordination, and Sol acceptance overhead.
- Use `Sol/Luna: Sol-only · reasoning/architecture task` when the core work is architecture, ambiguity resolution, requirements, trade-offs, orchestration, or a final decision owned by Sol.
- Use `Sol/Luna: Sol-only · no independent bounded work` when execution exists but cannot be separated safely or would create coupling and coordination overhead.
- `LUNA_UNAVAILABLE` is evidence-gated. Use `Sol/Luna: Sol-only · Luna unavailable` only when the current task's normal delegation path already naturally produced parent-visible execution evidence that a reasonable delegation opportunity could not proceed because the selector returned no valid Daily role or failed closed, or because the selected native Luna role, agent discovery, required Luna capability, or spawn/agent availability failed.
- The availability failure must be an observed execution fact from the current task. A selector that was not invoked, no child attempt, Sol retaining or completing the task, docs-only work, sequential dependencies, or no independent bounded work do not establish Luna unavailability. No delegation does not mean Luna unavailable.
- If current-task parent-visible availability failure evidence does not exist, do not use `LUNA_UNAVAILABLE`. It is never the default Sol-only fallback. Choose the most direct high-level non-availability reason supported by the observed task facts; when more than one seems plausible, use the one with the clearest parent-visible support.
- Generate the receipt only from facts already obtained during the task. Receipt generation must not invoke the selector, probe capabilities, spawn or inspect a child, read files, call tools or networks, access the network, write state or repository content, or add telemetry solely to produce it.
- The receipt is a user-facing execution summary, not runtime attestation. It may expose only delegated or Sol-only, the actual role, direct child count, actual parallel status, and one high-level reason label. Never expose hidden chain-of-thought, detailed internal reasoning, scratchpads, token or context counts, private instructions, sensitive paths or configuration, the full Task Contract, or child internal reasoning.

## Natural-language status and diagnostics

- When the user asks to check Sol/Luna status, run `<STATUS_COMMAND>` exactly once. Do not fetch ModelDial, create or refresh a profile or LKG, take the selector lock, spawn Luna, or write state.
- Render the returned whitelist as `Sol/Luna Status`: Version, Status, Today, Luna, Effort, Source, Fallback, Capability, Agents, Native leaf, Max parallel, and optional `ModelDial ref-cost` as `Luna <effort> vs Sol <effort> · ↓X.X%`.
- When today's selection is not initialized, render `Status Healthy`, `Today Selection not initialized`, `Luna Not selected`, `Effort Not selected`, `Source Not initialized`, and `Fallback`/`Capability` as `N/A`.
- When the user asks to generate a Sol/Luna diagnostic report, run the same `<STATUS_COMMAND>` exactly once and return its sanitized whitelist. Do not create a second health reader or include environment variables, configuration content, policy content, credentials, logs, exception messages, or arbitrary paths and URLs.

## Upgrade to the latest published version

- The request “upgrade Sol/Luna to the latest version” explicitly authorizes the latest published project version, including prereleases. Do not ask Stable or Preview again.
- Release discovery is a semantic workflow outside the installer. Request all pages of `/repos/SuperDaddyV/codex-sol-luna-worker/releases`; accept only entries with `draft = false`, non-null `published_at`, and a strict project SemVer tag.
- Reject build metadata, malformed leading zeroes, a mismatch between the Release prerelease flag and the SemVer prerelease, and duplicate Releases with the same normalized version. Choose by SemVer precedence, never by publication time.
- If the target is a prerelease, show this notice before any apply: `目标：<version>`; `渠道：Prerelease / Public Beta`; `此版本可能包含尚未完成的变化，外部真实运行验证少于稳定版。`; `修改托管文件前会创建事务备份；不会有意覆盖与本项目无关的用户配置。`
- Resolve the Release tag through its direct ref, peel either an annotated or lightweight tag to one exact 40-hex commit, acquire a detached checkout, then read the tag again. If it moved, fail closed as `TAG_MOVED`.
- Before apply, verify detached `HEAD`, installer `VERSION`, the Release tag, and the setup/source contract all identify the same target. Pass the verified commit to the installer as `--source-commit <40hex>`; never install from `master`, `target_commitish`, another mutable branch, or an unverified tag.
- If the installed version is already the target, perform zero writes and zero backups. If the installed version is newer by SemVer precedence, never downgrade automatically.

## Luna

- Luna performs bounded execution only; it does not own architecture or final acceptance.
- Each Luna custom-agent configuration enforces native leaf behavior with `[agents] enabled = false`.

## Task Contract

- Goal
- Scope
- Constraints
- Acceptance Criteria
- Verification

## Context Firewall

- Pass only the minimum context required by the bounded task.

## Parallelism and acceptance

- Run at most three Luna agents concurrently, and only for independent tasks.
- Sol reviews every Luna result and owns final acceptance.
