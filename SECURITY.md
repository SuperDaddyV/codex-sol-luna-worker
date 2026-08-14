# Security Policy

## Release boundary

`v4.1.0-rc4` is the published prerelease and current preview, with recorded real-upgrade and Runtime Cases A/B/C/D acceptance `PASS`; `v4.0.0` remains stable. RC4 changes only the installer-managed Global `AGENTS.md` policy payload, manifest version and owned hash, tests, and documentation. Publication does not perform an implicit installation, modify global Codex configuration during routine validation, manage credentials, or provide a production security boundary. Any real global runtime operation requires separate authorization, and recorded acceptance is not a security guarantee or a claim that every environment passed. Three-platform CI remains source validation and does not establish real Codex runtime validation on every platform, client, account, or user.

## Data and network behavior

- Project development state is repo-local under ignored `.var/`. Global runtime state uses an explicit `<CODEX_HOME>/sol-luna-v4/state` root and never depends on the current working directory.
- The selector's optional live mode sends an unauthenticated HTTPS GET first to the official ModelDial API v1 endpoint and, only when that response is unavailable or invalid, to the official full snapshot JSON. The host allowlist remains limited to `modeldial.com` and `reference.modeldial.com`.
- Radar HTML is not a v4.1 runtime source. The selector adds no third-party host, retry service, background refresh, or persistent HTTP cache.
- The selector does not send cookies, credentials, auth headers, repository content, prompts, or Codex session data.
- The Delegation Receipt is generated only from task facts already visible to Sol. `Luna unavailable` requires current-task parent-visible selector or native-agent availability failure evidence and is never the default fallback. Receipt generation adds no selector or network call, capability probe, tool, child creation or inspection, persistent state, telemetry, repository write, or private reasoning. Its one-line text is not runtime attestation.
- CI uses fixtures and does not contact ModelDial or run Codex.
- ModelDial-derived fixtures are attributed under CC BY 4.0 in `fixtures/modeldial/README.md`; repository source code remains under the project MIT license.

## Installation safety

`scripts/install.py` defaults to planning. Mutating modes require an explicit `--codex-home`, fail closed on unsafe merges or ownership conflicts, and create and verify a centralized backup before writes. Global policy is rendered from a dedicated template. RC4 treats an existing valid RC3 installation as a normal v4 upgrade and updates only the managed Global policy block plus manifest version and ownership metadata; selector, agents, configuration, state, and migration behavior remain unchanged. Legacy migration accepts only exact version `3.2`, does not convert state or access ModelDial, preserves unowned audit bundles, and writes the v4 manifest last with atomic replacement. Post-commit old-manifest cleanup is independently retryable. Repository-local writes additionally require `--validation-sandbox` below `.tmp/installer-validation/`. Routine lifecycle validation uses fake homes. Any real global migration remains a separate, explicitly approved maintenance action; publishing a source release never authorizes installation or cleanup of legacy evidence.

`CODEX_SOL_LUNA_SETUP.md` is client-side automation guidance, not a server-side security boundary. Review the setup contract before execution and use the immutable commit-pinned raw URL from the README. The contract must not widen permissions, replace the installer's transaction, or guess ownership; unknown ownership remains a fail-closed condition.

## Reporting

Do not include secrets, credentials, private session transcripts, or personal filesystem paths in a report. For this public repository, use GitHub's private vulnerability reporting channel when enabled.
