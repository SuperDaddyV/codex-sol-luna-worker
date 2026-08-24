# Security Policy

## Release boundary

`v4.1.1` is the current Stable release and default installation target.
Stable runtime Source Commit A2 is
`ca8e9e4caf5564ffe8d0a11fe376047594f8a748`; exact-SHA source CI passed on
Windows, Ubuntu, and macOS. The final bilingual README pins the reviewed
`CODEX_SOL_LUNA_INSTALL_ASSIST.md` contract through one exact immutable
documentation commit. That contract pins this reviewed
`CODEX_SOL_LUNA_SETUP.md` through an earlier exact immutable documentation
commit. Neither documentation commit is the runtime source or is passed to the
installer; no commit is required to self-reference its own SHA.
`v4.1.0` remains the previous immutable Stable release.
`v4.1.0-rc6` remains an immutable historical Prerelease / Preview / Public
Beta, and `v4.1.0-rc5` is an older historical Preview. The documented-environment RC5 O1-O10 record remains
bounded historical evidence; RC5 Final O4/O9 re-certification was not obtained
due to `CODEX_ROLLOUT_EVIDENCE_COMPATIBILITY`, with no confirmed product-runtime
regression. RC6 independently passed its recorded real Global upgrade,
fresh-task O1-O10 acceptance, Final O4/O9 re-certification, and Runtime Cases
A/B/C/D in one native Windows Codex environment. The real protected Sol/Luna
state and root identity remained unchanged during acceptance, observed unknown
paths were zero, and owned acceptance residuals were zero. These facts are
environment- and scenario-bounded evidence, not a security guarantee or
universal compatibility claim. Stable preserves the accepted RC6 product
payload byte-for-byte and advances only installed manifest version/source
metadata; after explicit Daily selection initialization, an independent
one-run pre-publication compatibility smoke passed all six component checks and
final Compatibility against that unchanged installed runtime. No real Global
`v4.1.1` installer apply was performed. Stable publication is independently
established only by the immutable `v4.1.1` tag and a non-draft, non-prerelease
GitHub Release. The immutable `v4.1.0` Stable and RC6 historical Prerelease
remain unchanged. RC4 remains
historical release evidence for Receipt reason evidence-gating.

## v4.1.2 candidate boundary

`v4.1.2` is an unreleased candidate on `master`; `v4.1.1` remains the current
Stable release and default installation target. No `v4.1.2` tag or Release is
established by source publication or CI alone.

Candidate Source Commit A `551520c2435aca94d60132f292edbd53cc975cbe`
passed exact-SHA CI run `32717295801` on Windows, Ubuntu, and macOS. This is
repository source validation only; it does not establish a real Global install,
real authentication, runtime acceptance, a tag, or a Release.

The candidate replaces production child-process ambient inheritance with
purpose-specific allowlists. Local version, selector, proof, and source checks
receive only cross-platform runtime variables and explicit process settings.
Codex network children additionally receive the supported authentication,
workload identity, proxy, and CA-certificate variables they require. Selected
custom-provider and enabled MCP environment names are extracted by name from
the explicit `CODEX_HOME/config.toml`; their values are never printed or
recorded. Invalid or aliased configuration, provider `auth.command`, and an
external Codex SQLite home fail closed rather than falling back to the full
parent environment.

Installer-owned path validation also rejects symlinks, Windows reparse points,
mount points, and cross-device aliases before managed writes. An ordinary file
that blocks the backup root remains a backup-creation failure, preserving the
same public reason code on Windows, Linux, and macOS.

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

`v4.1.1` preserves the RC6 selector behavior, including normalization of
malformed URL parsing, hostname, and port `ValueError` cases to
`SnapshotInvalid`. The installer payload version moves from `v4.1.0` to
`v4.1.1`, but a `v4.1.0`→`v4.1.1` apply changes only the ownership manifest.
The installation assistant, compatibility smoke, and acceptance harness are
tooling only and do not modify product runtime by themselves. The mutable
acceptance contract is limited to
`CODEX_SOL_LUNA_SETUP.md`, `RUNTIME_TESTS.md`, `ARCHITECTURE.md`, and this file.
`V410_TO_V411_INSTALLED_BEHAVIOR_CHANGED = NO`;
`ACCEPTANCE_CONTRACT_CHANGED = YES`.

`scripts/accept_rc5_runtime_isolation.py` requires an explicit real
`CODEX_HOME` audit root but installs the historical RC6 Source Commit A only into a fresh fake
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
historical RC6 attribution. Runtime changes are classified only inside the isolated home.
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
evidence, and classifies unknown or unsafe writes fail closed. By itself it does
not run the real Global upgrade or certify O1-O10 or Final O4/O9, and it does
not modify product runtime. Historical RC6 runtime acceptance therefore retained separate
O1-O10, Final O4/O9, and Runtime Cases A/B/C/D gates.

## Installation safety

`scripts/install.py --dry-run` executes the same payload, ownership, and effective-operation preflight as apply but performs no writable probe, backup, managed-file mutation, or manifest mutation. Mutating modes require an explicit `--codex-home`, fail closed on unsafe merges or ownership conflicts, and create and verify a centralized backup before writes. Stable accepts only an optional exact 40-hex `--source-commit`; malformed input fails before backup, write, or probe. A same-version idempotent run may preserve an existing valid SHA, while a version upgrade without the option never inherits an older source SHA. `v4.1.0`→`v4.1.1` lifecycle tests require only the ownership manifest to change and verify zero-write dry-run, backup, idempotency, exact rollback, downgrade refusal, and ownership conflict fail-closed behavior.

The assisted installation wrapper aggregates independent read-only prerequisite
failures and permits only bounded no-write or current-session recovery without
another approval. Package installation, elevation, and persistent environment
changes require an exact official-source proposal and explicit user approval.
Authentication, credentials, proxies, certificate trust, sandbox settings,
organization policy, exact-source checks, and installer ownership checks are
never auto-repair targets. Deterministic remediation runs once; transient
GitHub HTTPS checks have a bounded retry budget. The wrapper cannot replace or
weaken the transactional setup contract.

The natural-language latest-version workflow accepts only published non-draft strict SemVer releases, resolves and peels the selected tag to an immutable commit, detects tag movement, verifies detached `HEAD`, installer version, and setup/source alignment, and passes that exact SHA to the installer. Release discovery remains outside the installer; there is no auto-updater, background service, or mutable-branch apply. Legacy migration accepts only exact version `3.2`, does not convert state or access ModelDial, preserves unowned audit bundles, and writes the v4 manifest last with atomic replacement. Repository-local lifecycle validation uses fake homes. Any real global migration remains a separate, explicitly approved maintenance action.

`CODEX_SOL_LUNA_INSTALL_ASSIST.md` and `CODEX_SOL_LUNA_SETUP.md` are client-side automation guidance, not server-side security boundaries. Review both contracts before execution and use the immutable commit-pinned raw assisted-installation URL from the README. Neither contract may widen permissions, replace the installer's transaction, or guess ownership; unknown ownership remains a fail-closed condition.

The `v4.1.1` Stable installation assistant preserves that boundary. It
creates no preflight state file, binds approval to a SHA-256 identity covering
the exact blockers, commands, official sources, scope, impact, proof, and
rollback route, and executes approved recovery as argument vectors without a
shell. Its recovery catalog accepts only fixed official HTTPS domains; a
changed or invalid catalog fails closed. Authentication, proxy, certificate,
firewall, organization-policy, unsupported Linux Python, and Codex sign-in
cases remain guided user actions. The five-effort Luna probe is ephemeral,
ignores user configuration, uses the read-only sandbox, and runs before any
real `CODEX_HOME` installer dry-run or write. Support reports are generated
from a fixed whitelist and symbolize the target as `<CODEX_HOME>`. P3
standalone bootstrap is excluded, so the assistant never claims it can run
without a usable Python interpreter or immutable source checkout. These
controls do not change the installed selector, policy, agents, or config.

The Stable assistant adds an explicit post-reload `SELECTOR_INITIALIZATION` handoff.
The assistant does not perform that write implicitly: the displayed canonical
`--ensure-daily --print-selection` command invokes the installed selector's
normal managed-state transaction and must return an allowed role and matching
effort. Failure or incomplete proof stops without automatic retry. The
compatibility smoke cannot initialize Daily selection itself; it remains
read-only and status-only.

## Reporting

Do not include secrets, credentials, private session transcripts, or personal filesystem paths in a report. For this public repository, use GitHub's private vulnerability reporting channel when enabled.
