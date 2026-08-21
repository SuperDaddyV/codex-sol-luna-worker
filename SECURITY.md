# Security Policy

## Release boundary

`v4.1.0-rc6` is a master-tree source candidate, not tagged, published, Stable,
or the default installation target. RC6 Source Commit A is
`50ff886d1004ac3dd43b1f4ce531a2a8af8f7a49`; exact-SHA CI passed on Windows,
Ubuntu, and macOS. Its immutable candidate setup contract is documentation
Commit `86424ea4d6f6630a34b6e4daa22d2d93a5576ddf`; it is not the default entry or
runtime source. The published/default Preview remains `v4.1.0-rc5` through
immutable setup anchor `ccd9d84da2f74df9ca2d919729b75eebf2dac27a`, and
`v4.0.0` remains Stable. The documented-environment RC5 O1-O10 record remains
bounded evidence; Final O4/O9 re-certification was not obtained due to
`CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`; no confirmed product-runtime
regression is reported. RC6 real Global upgrade and O1-O10 acceptance were not
run. These facts are not a security guarantee, final PASS, or release claim.
RC4 remains historical release evidence for Receipt reason evidence-gating.

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

RC6 changes product runtime behavior only in `src/selector.py` by normalizing
malformed URL parsing, hostname, and port `ValueError` cases to
`SnapshotInvalid`; the installer payload version moves to `v4.1.0-rc6`.
The compatibility smoke and acceptance harness are tooling only and do not
modify product runtime. The mutable acceptance contract is limited to
`CODEX_SOL_LUNA_SETUP.md`, `RUNTIME_TESTS.md`, `ARCHITECTURE.md`, and this file.
`PRODUCT_RUNTIME_CHANGED = YES`; `ACCEPTANCE_CONTRACT_CHANGED = YES`.

`scripts/accept_rc5_runtime_isolation.py` requires an explicit real
`CODEX_HOME` audit root but installs the RC6 Source Commit A only into a fresh fake
home. Before the first installer write or authentication copy, it verifies that
the temporary parent and planned acceptance root are plain, non-overlapping
paths with no user-controlled symlink, junction, reparse point, mount, or
hardlink redirection to the real runtime. The fixed macOS `/var` system alias is
recognized for canonical platform temp directories. Authentication data is
copied with exclusive creation to a distinct fake-home file identity; its bytes
are never printed or committed. The Codex child inherits only a fixed minimal
non-credential environment; `CODEX_HOME`, `HOME`, and `USERPROFILE` point to the
fake home, while `APPDATA`, `LOCALAPPDATA`, temporary variables, and all `XDG_*`
locations, including `XDG_RUNTIME_DIR`, are redirected into an
acceptance-owned isolated runtime root instead of inheriting the user's real
locations. One
`isolated_runtime_env` is passed explicitly to selector, `codex exec`,
installer, and repository subprocesses. O9 fail-soft and status/health checks
run in-process under that same mapping and restore the caller environment, so
no O4/O9 execution path inherits the real process environment.

The real `CODEX_HOME` is audited only for immutable managed Sol/Luna state
(`PROTECTED_SOL_LUNA_STATE`) and root identity. The entire
`sol-luna-v4/state/**` tree, including Daily Profile, LKG, `selector.lock`, and
other state contents, is compared for hash, type, device/file identity, link
count, and reparse status. Unrelated real-home runtime activity is not used for
RC6 attribution. Runtime changes are classified only inside the isolated home.
`CODEX_PLATFORM_RUNTIME_STATE` retains the existing
explicit session, session-index, app-cache, and active-exec paths and adds only
the exact root-level `.sandbox_migration` safe regular file; the exact
`skills/**` and `plugins/.remote-plugin-install-staging/**` trees with safe
ordinary objects; the exact `browser/sessions`, `cache/remote_plugin_catalog`,
`plugins/cache`, and `tmp/arg0` trees; plus a structurally validated
visualization subtree. The remote-plugin staging root may persist empty after
normal cleanup, but its broader `plugins/**` parent is not allowed. Root
SQLite storage accepts only the named `goals`, `logs`, `memories`, `queue`,
`state`, and `thread_history` ID families, with `-wal` and `-shm` sidecars bound
to a safe base. Internal plugin-cache directory reparses use the same
resolved-target contract in real-home and isolated-home validation; external,
protected, escaping, and looping targets are rejected. Reparses are not allowed
in the staging or skills trees. Unsupported path types,
unexpected hardlinks, protected-state changes, and isolated writes outside the explicit
categories fail closed. The result reports only inventory metadata, hashes,
classifications, and symbolic category names, not credentials or real
authentication content. Before JSON
is printed, known real, isolated, temporary, repository, and executable paths
are replaced by symbolic locations and any remaining user-home path shape or
credential-shaped value is redacted.

Cleanup is ownership-gated: the target must remain the same direct
harness-prefixed child of the validated temporary parent, retain the original
directory identity, and contain the matching per-run marker and token. Cleanup
does not follow reparse entries and fails closed on an ownership or identity
mismatch. Regression coverage includes success and failure cleanup, symlink,
Windows junction, mount-point, and hardlink cases.

The compatibility-smoke baseline is read-only for the repository and managed
selector state. It checks dual exact rollout roots and bounded writer-settle
evidence, and classifies unknown or unsafe writes fail closed. It does not run
the real Global upgrade, does not certify O1-O10 or Final O4/O9, and does not
modify product runtime.

## Installation safety

`scripts/install.py --dry-run` now executes the same payload, ownership, and effective-operation preflight as apply but performs no writable probe, backup, managed-file mutation, or manifest mutation. Mutating modes require an explicit `--codex-home`, fail closed on unsafe merges or ownership conflicts, and create and verify a centralized backup before writes. RC6 accepts only an optional exact 40-hex `--source-commit`; malformed input fails before backup, write, or probe. A same-version idempotent run may preserve an existing valid SHA, while a version upgrade without the option never inherits an older source SHA.

The natural-language latest-version workflow accepts only published non-draft strict SemVer releases, resolves and peels the selected tag to an immutable commit, detects tag movement, verifies detached `HEAD`, installer version, and setup/source alignment, and passes that exact SHA to the installer. Release discovery remains outside the installer; there is no auto-updater, background service, or mutable-branch apply. Legacy migration accepts only exact version `3.2`, does not convert state or access ModelDial, preserves unowned audit bundles, and writes the v4 manifest last with atomic replacement. Repository-local lifecycle validation uses fake homes. Any real global migration remains a separate, explicitly approved maintenance action.

`CODEX_SOL_LUNA_SETUP.md` is client-side automation guidance, not a server-side security boundary. Review the setup contract before execution and use the immutable commit-pinned raw URL from the README. The contract must not widen permissions, replace the installer's transaction, or guess ownership; unknown ownership remains a fail-closed condition.

## Reporting

Do not include secrets, credentials, private session transcripts, or personal filesystem paths in a report. For this public repository, use GitHub's private vulnerability reporting channel when enabled.
