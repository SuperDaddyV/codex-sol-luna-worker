import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.child_environment import ChildEnvironmentError, build_child_environment
from scripts.probe_capabilities import EFFORTS, build_command, run_probe


class CapabilityProbeTests(unittest.TestCase):
    def test_commands_are_ephemeral_and_ignore_user_config(self):
        command = build_command("codex", "max")
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--strict-config", command)
        self.assertIn('model_reasoning_effort="max"', command)

    @patch("scripts.probe_capabilities.subprocess.run")
    def test_successful_client_run_is_supported_even_if_echo_is_not_exact(self, run):
        calls = []
        for effort in EFFORTS:
            marker = f"LUNA_CAPABILITY_{effort.upper()}_OK"
            output = marker if effort != "high" else f"Result: {marker}"
            calls.append(subprocess.CompletedProcess([], 0, output, ""))
        calls.append(subprocess.CompletedProcess([], 0, "codex-cli fixture", ""))
        run.side_effect = calls

        result = run_probe("codex", timeout=1)

        self.assertTrue(result["all_supported"])
        high = next(item for item in result["results"] if item["effort"] == "high")
        self.assertTrue(high["supported"])
        self.assertFalse(high["response_exact"])

    @patch("scripts.probe_capabilities.subprocess.run")
    def test_probe_children_use_purpose_minimal_environments(self, run):
        observed = []

        def execute(command, **kwargs):
            observed.append((command, kwargs["env"]))
            if command[1] == "--version":
                return subprocess.CompletedProcess(command, 0, "codex-cli fixture", "")
            return subprocess.CompletedProcess(command, 0, "probe fixture", "")

        run.side_effect = execute
        parent = {
            "PATH": "fixture-path",
            "PATHEXT": ".EXE;.CMD",
            "SYSTEMROOT": "C:\\Windows",
            "HOME": "/fixture/home",
            "USERPROFILE": "C:\\Users\\fixture",
            "APPDATA": "C:\\Users\\fixture\\AppData\\Roaming",
            "TEMP": "C:\\Temp",
            "XDG_CONFIG_HOME": "/fixture/xdg-config",
            "LANG": "en_US.UTF-8",
            "CODEX_HOME": "ambient-codex-home",
            "CODEX_API_KEY": "fixture-codex-key",
            "CODEX_ACCESS_TOKEN": "fixture-access-token",
            "OPENAI_FEDERATION_RULE_ID": "fixture-rule",
            "OPENAI_IDENTITY_TOKEN_FILE": "/fixture/identity-token",
            "OPENAI_WORKLOAD_IDENTITY_CONTEXT": '{"fixture":"context"}',
            "HTTP_PROXY": "http://fixture-proxy",
            "https_proxy": "http://fixture-lower-proxy",
            "NO_PROXY": "localhost",
            "CODEX_CA_CERTIFICATE": "/fixture/codex-ca.pem",
            "SSL_CERT_FILE": "/fixture/ssl-ca.pem",
            "UNRELATED_SENTINEL_SECRET": "must-not-cross",
        }

        run_probe(
            "codex",
            timeout=1,
            codex_home=Path("explicit-codex-home"),
            source_environment=parent,
        )

        self.assertEqual(len(observed), len(EFFORTS) + 1)
        for _command, environment in observed:
            self.assertNotIn("UNRELATED_SENTINEL_SECRET", environment)
            self.assertEqual(environment["CODEX_HOME"], "explicit-codex-home")
            self.assertEqual(environment["PATH"], "fixture-path")
            self.assertEqual(environment["HOME"], "/fixture/home")
            self.assertEqual(environment["USERPROFILE"], "C:\\Users\\fixture")
        for _command, environment in observed[: len(EFFORTS)]:
            for name in (
                "CODEX_API_KEY",
                "CODEX_ACCESS_TOKEN",
                "OPENAI_FEDERATION_RULE_ID",
                "OPENAI_IDENTITY_TOKEN_FILE",
                "OPENAI_WORKLOAD_IDENTITY_CONTEXT",
                "HTTP_PROXY",
                "https_proxy",
                "NO_PROXY",
                "CODEX_CA_CERTIFICATE",
                "SSL_CERT_FILE",
            ):
                self.assertIn(name, environment)
        version_environment = observed[-1][1]
        self.assertNotIn("CODEX_API_KEY", version_environment)
        self.assertNotIn("HTTP_PROXY", version_environment)
        self.assertNotIn("SSL_CERT_FILE", version_environment)

    def test_provider_environment_names_are_preserved_without_ambient_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            (codex_home / "config.toml").write_text(
                'model_provider = "fixture"\n'
                '[model_providers.fixture]\n'
                'env_key = "FIXTURE_PROVIDER_TOKEN"\n'
                'env_http_headers = { "X-Tenant" = "FIXTURE_TENANT" }\n',
                encoding="utf-8",
            )
            environment = build_child_environment(
                codex_home=codex_home,
                source={
                    "PATH": "fixture-path",
                    "CODEX_HOME": "ambient-codex-home",
                    "FIXTURE_PROVIDER_TOKEN": "fixture-provider-token",
                    "FIXTURE_TENANT": "fixture-tenant",
                    "UNRELATED_SENTINEL_SECRET": "must-not-cross",
                },
                network=True,
                include_config_environment=True,
            )

        self.assertEqual(environment["CODEX_HOME"], str(codex_home))
        self.assertEqual(
            environment["FIXTURE_PROVIDER_TOKEN"], "fixture-provider-token"
        )
        self.assertEqual(environment["FIXTURE_TENANT"], "fixture-tenant")
        self.assertNotIn("UNRELATED_SENTINEL_SECRET", environment)

    def test_invalid_provider_configuration_fails_closed(self):
        fixtures = (
            'model_provider = "missing"\n',
            'model_provider = "fixture"\n'
            '[model_providers.fixture]\nenv_key = 1\n',
            'model_provider = "fixture"\n'
            '[model_providers.fixture]\nenv_key = "BAD=NAME"\n',
            '[model_providers.fixture\n',
        )
        for content in fixtures:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as temporary:
                codex_home = Path(temporary)
                (codex_home / "config.toml").write_text(
                    content,
                    encoding="utf-8",
                )
                with self.assertRaises(ChildEnvironmentError):
                    build_child_environment(
                        codex_home=codex_home,
                        source={"PATH": "fixture-path"},
                        network=True,
                        include_config_environment=True,
                    )

    def test_enabled_mcp_environment_names_are_preserved_explicitly(self):
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            (codex_home / "config.toml").write_text(
                '[mcp_servers.fixture]\n'
                'bearer_token_env_var = "FIXTURE_MCP_BEARER"\n'
                'env_http_headers = { "X-Tenant" = "FIXTURE_MCP_TENANT" }\n'
                'env_vars = ["FIXTURE_MCP_LOCAL", '
                '{ name = "FIXTURE_MCP_REMOTE", source = "remote" }]\n'
                '[mcp_servers.disabled]\n'
                'enabled = false\n'
                'bearer_token_env_var = "DISABLED_MCP_BEARER"\n',
                encoding="utf-8",
            )
            environment = build_child_environment(
                codex_home=codex_home,
                source={
                    "PATH": "fixture-path",
                    "FIXTURE_MCP_BEARER": "fixture-bearer",
                    "FIXTURE_MCP_TENANT": "fixture-tenant",
                    "FIXTURE_MCP_LOCAL": "fixture-local",
                    "FIXTURE_MCP_REMOTE": "fixture-remote",
                    "DISABLED_MCP_BEARER": "disabled-bearer",
                    "UNRELATED_SENTINEL_SECRET": "must-not-cross",
                },
                network=True,
                include_config_environment=True,
            )

        self.assertEqual(environment["FIXTURE_MCP_BEARER"], "fixture-bearer")
        self.assertEqual(environment["FIXTURE_MCP_TENANT"], "fixture-tenant")
        self.assertEqual(environment["FIXTURE_MCP_LOCAL"], "fixture-local")
        self.assertNotIn("FIXTURE_MCP_REMOTE", environment)
        self.assertNotIn("DISABLED_MCP_BEARER", environment)
        self.assertNotIn("UNRELATED_SENTINEL_SECRET", environment)

    def test_provider_auth_command_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            (codex_home / "config.toml").write_text(
                'model_provider = "fixture"\n'
                '[model_providers.fixture.auth]\n'
                'command = "fixture-auth-helper"\n',
                encoding="utf-8",
            )
            with self.assertRaises(ChildEnvironmentError):
                build_child_environment(
                    codex_home=codex_home,
                    source={"PATH": "fixture-path"},
                    network=True,
                    include_config_environment=True,
                )

    def test_codex_sqlite_home_is_bounded_to_explicit_codex_home(self):
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary).resolve()
            environment = build_child_environment(
                codex_home=codex_home,
                source={
                    "PATH": "fixture-path",
                    "CODEX_SQLITE_HOME": str(codex_home),
                    "UNRELATED_SENTINEL_SECRET": "must-not-cross",
                },
                network=True,
                include_config_environment=True,
            )
            self.assertEqual(
                environment["CODEX_SQLITE_HOME"],
                str(codex_home),
            )
            self.assertNotIn("UNRELATED_SENTINEL_SECRET", environment)

            for source, config in (
                ({"CODEX_SQLITE_HOME": str(codex_home / "external")}, ""),
                ({}, 'sqlite_home = "external"\n'),
            ):
                with self.subTest(source=source, config=config):
                    (codex_home / "config.toml").write_text(
                        config,
                        encoding="utf-8",
                    )
                    with self.assertRaises(ChildEnvironmentError):
                        build_child_environment(
                            codex_home=codex_home,
                            source={"PATH": "fixture-path", **source},
                            network=True,
                            include_config_environment=True,
                            child_cwd=codex_home,
                        )


if __name__ == "__main__":
    unittest.main()
