# Security Policy

## Release-candidate boundary

This release candidate does not install itself, modify global Codex configuration, manage credentials, or provide a production security boundary.

## Data and network behavior

- Runtime state is repo-local under `.var/` and is ignored by Git.
- The selector's optional live mode sends an unauthenticated HTTPS GET only to the strict ModelDial host allowlist.
- The selector does not send cookies, credentials, auth headers, repository content, prompts, or Codex session data.
- CI uses fixtures and does not contact ModelDial or run Codex.

## Installation safety

`scripts/install.py` supports planning only. It performs conflict detection and describes a backup location but has no apply mode. Review any future installation implementation separately before allowing writes to `<CODEX_HOME>`; the GitHub -> installer -> clean global validation path remains a pre-stable-release gate.

## Reporting

Do not include secrets, credentials, private session transcripts, or personal filesystem paths in a report. For a future public repository, use GitHub's private vulnerability reporting channel when enabled.
