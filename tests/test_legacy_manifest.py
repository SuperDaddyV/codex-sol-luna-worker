import json
import tempfile
import unittest
from pathlib import Path

from scripts.install import (
    InstallerError,
    LEGACY_VERSION,
    _legacy_relative,
    _load_legacy_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "legacy-v3" / "manifest-3.2.json"


class LegacyManifestTests(unittest.TestCase):
    def test_real_shape_32_manifest_is_supported(self):
        manifest = _load_legacy_manifest(FIXTURE)
        self.assertEqual(LEGACY_VERSION, "3.2")
        self.assertEqual(manifest["version"], "3.2")
        self.assertEqual(len(manifest["created_files"]), 24)
        self.assertIsInstance(manifest["backup_files"], dict)
        self.assertIn("validation", manifest)
        self.assertIn("pre_install_hashes", manifest)

    def test_owned_artifacts_are_safely_normalized(self):
        manifest = _load_legacy_manifest(FIXTURE)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / ".codex"
            normalized = [
                _legacy_relative(target, value) for value in manifest["created_files"]
            ]
        self.assertEqual(len(normalized), len(set(normalized)))
        self.assertIn("sol-luna-router/install-manifest.json", normalized)
        self.assertIn("hooks.json", normalized)

    def test_unknown_and_similar_versions_fail_closed(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for version in ("3.2.0", "3.2.1", "v3.2", "3.20", "unknown"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "manifest.json"
                candidate = dict(fixture)
                candidate["version"] = version
                path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.assertRaises(InstallerError) as raised:
                    _load_legacy_manifest(path)
                self.assertEqual(raised.exception.reason_code, "MANIFEST_INVALID")

    def test_malformed_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(
                json.dumps(
                    {
                        "version": "3.2",
                        "policy_version": "3.2",
                        "created_files": "not-a-list",
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(InstallerError) as raised:
                _load_legacy_manifest(path)
            self.assertEqual(raised.exception.reason_code, "MANIFEST_INVALID")


if __name__ == "__main__":
    unittest.main()
