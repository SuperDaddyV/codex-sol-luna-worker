"""Build least-privilege environments for production child processes."""

from __future__ import annotations

import os
import re
import stat
import tomllib
from pathlib import Path
from typing import Mapping, Sequence


RUNTIME_ENVIRONMENT_NAMES = frozenset(
    {
        "APPDATA",
        "COLORTERM",
        "COMSPEC",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "LANG",
        "LANGUAGE",
        "LC_ADDRESS",
        "LC_ALL",
        "LC_COLLATE",
        "LC_CTYPE",
        "LC_IDENTIFICATION",
        "LC_MEASUREMENT",
        "LC_MESSAGES",
        "LC_MONETARY",
        "LC_NAME",
        "LC_NUMERIC",
        "LC_PAPER",
        "LC_TELEPHONE",
        "LC_TIME",
        "LOCALAPPDATA",
        "LOGNAME",
        "NO_COLOR",
        "OS",
        "PATH",
        "PATHEXT",
        "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_ARCHITEW6432",
        "PROGRAMDATA",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMW6432",
        "SHELL",
        "SYSTEMROOT",
        "TEMP",
        "TERM",
        "TMP",
        "TMPDIR",
        "TZ",
        "USER",
        "USERNAME",
        "USERPROFILE",
        "WINDIR",
        "XDG_CACHE_HOME",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_RUNTIME_DIR",
        "XDG_STATE_HOME",
    }
)
TRANSPORT_ENVIRONMENT_NAMES = frozenset(
    {
        "ALL_PROXY",
        "CURL_CA_BUNDLE",
        "GIT_SSL_CAINFO",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_FILE",
    }
)
CODEX_NETWORK_ENVIRONMENT_NAMES = frozenset(
    {
        "CODEX_ACCESS_TOKEN",
        "CODEX_API_KEY",
        "CODEX_CA_CERTIFICATE",
        "OPENAI_FEDERATION_RULE_ID",
        "OPENAI_IDENTITY_TOKEN_FILE",
        "OPENAI_WORKLOAD_IDENTITY_CONTEXT",
    }
)
BUILTIN_MODEL_PROVIDERS = frozenset({"lmstudio", "ollama", "openai"})
ENVIRONMENT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ChildEnvironmentError(RuntimeError):
    """Raised when a minimal child environment cannot be built safely."""


def _load_config(codex_home: Path) -> Mapping[str, object]:
    config_path = codex_home / "config.toml"
    try:
        metadata = config_path.lstat()
    except FileNotFoundError:
        return {}
    except OSError:
        raise ChildEnvironmentError(
            "Codex configuration could not be inspected safely"
        ) from None
    if not stat.S_ISREG(metadata.st_mode):
        raise ChildEnvironmentError("Codex configuration is not a regular file")
    try:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        raise ChildEnvironmentError(
            "Codex configuration could not be parsed safely"
        ) from None
    if not isinstance(config, Mapping):
        raise ChildEnvironmentError("Codex configuration is invalid")
    return config


def _environment_name(value: object, *, field: str) -> str:
    if not isinstance(value, str) or ENVIRONMENT_NAME.fullmatch(value) is None:
        raise ChildEnvironmentError(f"{field} variable is invalid")
    return value


def _environment_header_names(value: object, *, field: str) -> set[str]:
    if not isinstance(value, Mapping):
        raise ChildEnvironmentError(f"{field} is invalid")
    return {
        _environment_name(env_name, field=field)
        for env_name in value.values()
    }


def _provider_environment_names(config: Mapping[str, object]) -> set[str]:
    selected_provider = config.get("model_provider", "openai")
    if not isinstance(selected_provider, str) or not selected_provider:
        raise ChildEnvironmentError("selected model provider is invalid")
    providers = config.get("model_providers", {})
    if not isinstance(providers, Mapping):
        raise ChildEnvironmentError("model provider configuration is invalid")
    if (
        selected_provider not in BUILTIN_MODEL_PROVIDERS
        and selected_provider not in providers
    ):
        raise ChildEnvironmentError("selected model provider is not configured")

    names: set[str] = set()
    if selected_provider in BUILTIN_MODEL_PROVIDERS:
        return names
    provider = providers[selected_provider]
    if not isinstance(provider, Mapping):
        raise ChildEnvironmentError("selected model provider entry is invalid")
    env_key = provider.get("env_key")
    if env_key is not None:
        names.add(_environment_name(env_key, field="provider env_key"))
    names.update(
        _environment_header_names(
            provider.get("env_http_headers", {}),
            field="provider env_http_headers",
        )
    )
    auth = provider.get("auth")
    if auth is not None:
        if not isinstance(auth, Mapping) or not isinstance(auth.get("command"), str):
            raise ChildEnvironmentError("provider auth command is invalid")
        raise ChildEnvironmentError(
            "provider auth command environment cannot be resolved safely"
        )
    return names


def _mcp_environment_names(config: Mapping[str, object]) -> set[str]:
    servers = config.get("mcp_servers", {})
    if not isinstance(servers, Mapping):
        raise ChildEnvironmentError("MCP server configuration is invalid")
    names: set[str] = set()
    for server in servers.values():
        if not isinstance(server, Mapping):
            raise ChildEnvironmentError("MCP server entry is invalid")
        enabled = server.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ChildEnvironmentError("MCP server enabled flag is invalid")
        if not enabled:
            continue
        bearer = server.get("bearer_token_env_var")
        if bearer is not None:
            names.add(_environment_name(bearer, field="MCP bearer token"))
        names.update(
            _environment_header_names(
                server.get("env_http_headers", {}),
                field="MCP env_http_headers",
            )
        )
        env_vars = server.get("env_vars", [])
        if not isinstance(env_vars, Sequence) or isinstance(env_vars, (str, bytes)):
            raise ChildEnvironmentError("MCP env_vars is invalid")
        for entry in env_vars:
            if isinstance(entry, str):
                names.add(_environment_name(entry, field="MCP env_vars"))
                continue
            if not isinstance(entry, Mapping):
                raise ChildEnvironmentError("MCP env_vars entry is invalid")
            name = _environment_name(entry.get("name"), field="MCP env_vars")
            source = entry.get("source", "local")
            if source not in {"local", "remote"}:
                raise ChildEnvironmentError("MCP env_vars source is invalid")
            if source == "local":
                names.add(name)
    return names


def _resolve_child_path(value: str, child_cwd: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = child_cwd / path
    return Path(os.path.abspath(path))


def _validate_sqlite_home(
    *,
    config: Mapping[str, object],
    codex_home: Path,
    source: Mapping[str, str],
    child_cwd: Path,
) -> str | None:
    configured = config.get("sqlite_home")
    if configured is not None and (not isinstance(configured, str) or not configured):
        raise ChildEnvironmentError("configured Codex SQLite home is invalid")
    ambient = _source_value(source, "CODEX_SQLITE_HOME")
    effective = configured if configured is not None else ambient
    if effective is None:
        return None
    effective_path = os.path.normcase(str(_resolve_child_path(effective, child_cwd)))
    expected_path = os.path.normcase(str(Path(os.path.abspath(codex_home))))
    if effective_path != expected_path:
        raise ChildEnvironmentError("external Codex SQLite home is unsupported")
    return ambient if configured is None else None


def _copy_configured_variable(
    environment: dict[str, str], source: Mapping[str, str], name: str
) -> None:
    value = source.get(name)
    if value is not None:
        environment[name] = value
        return
    if os.name == "nt":
        matching = next(
            (value for key, value in source.items() if key.upper() == name.upper()),
            None,
        )
        if matching is not None:
            environment[name] = matching


def _source_value(source: Mapping[str, str], name: str) -> str | None:
    value = source.get(name)
    if value is not None:
        return value
    if os.name == "nt":
        return next(
            (value for key, value in source.items() if key.upper() == name.upper()),
            None,
        )
    return None


def build_process_environment(
    *,
    source: Mapping[str, str] | None = None,
    transport: bool = False,
    extra_names: Sequence[str] = (),
) -> dict[str, str]:
    """Return a minimal environment for non-Codex production children."""

    inherited = os.environ if source is None else source
    allowed_names = set(RUNTIME_ENVIRONMENT_NAMES)
    if transport:
        allowed_names.update(TRANSPORT_ENVIRONMENT_NAMES)
    for name in extra_names:
        allowed_names.add(_environment_name(name, field="child environment"))
    return {
        name: value
        for name, value in inherited.items()
        if name.upper() in allowed_names
    }


def build_child_environment(
    *,
    codex_home: Path,
    source: Mapping[str, str] | None = None,
    network: bool = False,
    include_config_environment: bool = False,
    python_no_bytecode: bool = False,
    child_cwd: Path | None = None,
) -> dict[str, str]:
    """Return an explicit child environment without unrelated ambient values."""

    if include_config_environment and not network:
        raise ChildEnvironmentError(
            "Codex configuration environment requires a network child environment"
        )
    inherited = os.environ if source is None else source
    environment = build_process_environment(source=inherited, transport=network)
    if network:
        for name in CODEX_NETWORK_ENVIRONMENT_NAMES:
            _copy_configured_variable(environment, inherited, name)
    environment.pop("CODEX_HOME", None)
    environment.pop("PYTHONDONTWRITEBYTECODE", None)
    if include_config_environment:
        config = _load_config(codex_home)
        for name in _provider_environment_names(config) | _mcp_environment_names(config):
            _copy_configured_variable(environment, inherited, name)
        sqlite_home = _validate_sqlite_home(
            config=config,
            codex_home=codex_home,
            source=inherited,
            child_cwd=Path.cwd() if child_cwd is None else child_cwd,
        )
        if sqlite_home is not None:
            environment["CODEX_SQLITE_HOME"] = sqlite_home
    environment["CODEX_HOME"] = str(codex_home)
    if python_no_bytecode:
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment
