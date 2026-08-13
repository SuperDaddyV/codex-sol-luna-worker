# Sol Brain / Luna Worker Policy

## Scope and authority

- Sol is the sole planner, architect, orchestrator, ambiguity resolver, and final reviewer.
- Luna agents are bounded execution workers. They do not redefine architecture, expand scope, control delegation, or make the final acceptance decision.
- Keep source, test, and documentation changes inside this repository. Do not modify the real Global `CODEX_HOME` unless the user explicitly authorizes a specific runtime operation; do not run installer apply or clean real runtime state or backups on your own.
- Native Codex custom agents are the orchestration mechanism. Do not add Hook routing or a custom orchestration engine.

## Daily Luna role

For actual project delegation, follow the inherited Global policy and its installed selector for the current Beijing-day Luna role. Project policy must not maintain a second Daily role authority.

- Repository-local `.var/` selector state is development-only and non-authoritative for actual Codex project delegation.
- When the inherited Global selector returns a valid role, delegate only through that native custom agent type: `luna_low`, `luna_medium`, `luna_high`, `luna_xhigh`, or `luna_max`.
- If the inherited Global selector yields no valid Luna role, Sol retains the work. Do not guess an effort or substitute a direct model or reasoning-effort override.
- Never select `ultra` for Luna.

## Delegation boundary

Prefer the selected Luna role for clear, bounded execution work such as implementation, targeted search, tests, lint, build, repetitive edits, and read-heavy extraction.

Sol should handle work directly when delegation overhead exceeds the task, including one-line edits, trivial reads, and a single simple tool call.

Delegate with the smallest useful Task Contract:

```text
Goal
Scope
Constraints
Acceptance Criteria
Verification
```

Apply a context firewall: send only the files, facts, constraints, and acceptance criteria required for the bounded task. Do not dump the full parent conversation.

## Parallelism

- Parallelize only genuinely independent tasks.
- Keep at most three spawned threads open concurrently.
- Avoid parallel writers on overlapping files.

## Luna leaf behavior

- Luna completes only the bounded task from Sol and returns concise results with verification evidence.
- Luna must not spawn, organize, or delegate to other agents.
- Ambiguity, scope conflicts, and architecture decisions return to Sol.
- Each stable Luna custom-agent configuration enforces native leaf behavior with `[agents] enabled = false`.
- Native Runtime Test 4 verified that Luna children configured this way do not receive multi-agent or delegation tools.

## Acceptance and review loop

1. Sol defines acceptance criteria once.
2. Luna implements and self-tests the bounded task.
3. Sol performs a targeted review against the original criteria.
4. Fix only failures related to those criteria.
5. Record unrelated findings as follow-ups instead of widening the loop.

Sol alone declares the project or task complete.
