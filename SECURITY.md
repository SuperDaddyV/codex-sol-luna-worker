# Security Policy

## Release boundary

`v4.1.0-rc5 — Observability & UX` is a source candidate, not a published release. `v4.1.0-rc4` remains the published prerelease and current preview, with recorded real-upgrade and Runtime Cases A/B/C/D acceptance `PASS`; `v4.0.0` remains stable. RC5 Source Commit A and its separately authorized O1-O10 runtime acceptance are now recorded, but neither source validation nor the bounded acceptance is a security guarantee or a claim that every environment passed. Three-platform CI remains source validation and does not establish real Codex runtime validation on every platform, client, account, or user. No tag, release, or Stable promotion is implied.

## Data and network behavior

- Project development state is repo-local under ignored `.var/`. Global runtime state uses an explicit `<CODEX_HOME>/sol-luna-v4/state` root and never depends on the current working directory.
- The selector's optional live mode sends an unauthenticated HTTPS GET first to the official ModelDial API v1 endpoint and, only when that response is unavailable or invalid, to the official full snapshot JSON. The host allowlist remains limited to `modeldial.com` and `reference.modeldial.com`.
- Radar HTML is not a v4.1 runtime source. The selector adds no third-party host, retry service, background refresh, or persistent HTTP cache.
- The selector does not send cookies, credentials, auth headers, repository content, prompts, or Codex session data.
- The Delegation Receipt is generated only from task facts already visible to Sol. `Luna unavailable` requires current-task parent-visible selector or native-agent availability failure evidence and is never the default fallback. Receipt generation adds no selector or network call, capability probe, tool, child creation or inspection, persistent state, telemetry, repository write, or private reasoning. Its one-line text is not runtime attestation.
- RC5 reference cost is optional same-batch, same-pricing, same-effort ModelDial configuration metadata. It is not token accounting, a billing claim, whole-task savings, quota measurement, or telemetry. Invalid cost metadata is omitted without affecting valid score selection.
- Status is a read-only inspection of a fixed installed-file and existing-profile set. Diagnostic output is built from an exact whitelist, replaces filesystem paths with symbolic locations, accepts a commit SHA only when it is exactly 40 hex characters, and applies a final path, URL, and secret-canary sanitizer. It never emits environment variables, configuration or policy content, credentials, cookies, headers, logs, arbitrary exception messages, or child reasoning.
- CI uses fixtures and does not contact ModelDial or run Codex.
- ModelDial-derived fixtures are attributed under CC BY 4.0 in `fixtures/modeldial/README.md`; repository source code remains under the project MIT license.

## Runtime acceptance harness safety

`scripts/accept_rc5_runtime_isolation.py` requires an explicit real
`CODEX_HOME` audit root but installs Source Commit A only into a fresh fake
home. Before the first installer write or authentication copy, it verifies that
the temporary parent and planned acceptance root are plain, non-overlapping
paths with no user-controlled symlink, junction, reparse point, mount, or
hardlink redirection to the real runtime. The fixed macOS `/var` system alias is
recognized for canonical platform temp directories. Authentication data is
copied with exclusive creation to a distinct fake-home file identity; its bytes
are never printed or committed. The Codex child inherits only a fixed minimal
non-credential environment; home,
application-data, temporary, and XDG locations are redirected into the fake
home instead of inheriting the user's real locations.

The audit distinguishes immutable managed Sol/Luna state
(`PROTECTED_SOL_LUNA_STATE`) from enumerated Codex platform runtime activity
(`CODEX_PLATFORM_RUNTIME_STATE`) and enumerated local storage activity
(`CODEX_LOCAL_STORAGE_STATE`). Unsupported path types, reparse escapes,
unexpected hardlinks, protected-state changes, and writes outside the explicit
categories fail closed. The result reports only inventory metadata, hashes,
classifications, and symbolic category names, not credentials or real
authentication content. Before JSON is printed, known real, fake, temporary,
repository, and executable paths are replaced by symbolic locations and any
remaining user-home path shape or credential-shaped value is redacted.

Cleanup is ownership-gated: the target must remain the same direct
harness-prefixed child of the validated temporary parent, retain the original
directory identity, and contain the matching per-run marker and token. Cleanup
does not follow reparse entries and fails closed on an ownership or identity
mismatch. Regression coverage includes success and failure cleanup, symlink,
Windows junction, mount-point, and hardlink cases.

## Installation safety

`scripts/install.py --dry-run` now executes the same payload, ownership, and effective-operation preflight as apply but performs no writable probe, backup, managed-file mutation, or manifest mutation. Mutating modes require an explicit `--codex-home`, fail closed on unsafe merges or ownership conflicts, and create and verify a centralized backup before writes. RC5 accepts only an optional exact 40-hex `--source-commit`; malformed input fails before backup, write, or probe. A same-version idempotent run may preserve an existing valid SHA, while a version upgrade without the option never inherits an older source SHA.

The natural-language latest-version workflow accepts only published non-draft strict SemVer releases, resolves and peels the selected tag to an immutable commit, detects tag movement, verifies detached `HEAD`, installer version, and setup/source alignment, and passes that exact SHA to the installer. Release discovery remains outside the installer; there is no auto-updater, background service, or mutable-branch apply. Legacy migration accepts only exact version `3.2`, does not convert state or access ModelDial, preserves unowned audit bundles, and writes the v4 manifest last with atomic replacement. Repository-local lifecycle validation uses fake homes. Any real global migration remains a separate, explicitly approved maintenance action.

`CODEX_SOL_LUNA_SETUP.md` is client-side automation guidance, not a server-side security boundary. Review the setup contract before execution and use the immutable commit-pinned raw URL from the README. The contract must not widen permissions, replace the installer's transaction, or guess ownership; unknown ownership remains a fail-closed condition.

## Reporting

Do not include secrets, credentials, private session transcripts, or personal filesystem paths in a report. For this public repository, use GitHub's private vulnerability reporting channel when enabled.
