# Security Policy

## Release-candidate boundary

This release candidate does not perform an implicit installation, modify global Codex configuration during validation, manage credentials, or provide a production security boundary.

## Data and network behavior

- Project development state is repo-local under ignored `.var/`. Global runtime state uses an explicit `<CODEX_HOME>/sol-luna-v4/state` root and never depends on the current working directory.
- The selector's optional live mode sends an unauthenticated HTTPS GET only to the strict ModelDial host allowlist.
- The selector does not send cookies, credentials, auth headers, repository content, prompts, or Codex session data.
- CI uses fixtures and does not contact ModelDial or run Codex.

## Installation safety

`scripts/install.py` defaults to planning. Mutating modes require an explicit `--codex-home`, fail closed on unsafe merges or ownership conflicts, and create and verify a centralized backup before writes. Global policy is rendered from a dedicated template. Legacy migration accepts only exact version `3.2`, does not convert state or access ModelDial, preserves unowned audit bundles, and writes the v4 manifest last with atomic replacement. Post-commit old-manifest cleanup is independently retryable. Repository-local writes additionally require `--validation-sandbox` below `.tmp/installer-validation/`. RC1 validation uses fake homes only; review and approve the global migration plan separately before allowing writes to a real `<CODEX_HOME>`.

## Reporting

Do not include secrets, credentials, private session transcripts, or personal filesystem paths in a report. For a future public repository, use GitHub's private vulnerability reporting channel when enabled.
