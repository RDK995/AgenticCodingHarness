#!/usr/bin/env python3
"""Tests for explicit paid-campaign authorization and provenance."""

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "check-campaign-manifest.py"


def load_module():
    spec = importlib.util.spec_from_file_location("campaign_manifest", PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CampaignManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def manifest(self):
        campaign_id = "01234567-89ab-cdef-0123-456789abcdef"
        return {
            "schema_version": 1,
            "campaign_id": campaign_id,
            "authorization": {
                "text": f"Authorize paid runtime-v3 campaign {campaign_id} up to $40",
                "max_cost_usd": 40,
            },
            "harness": {"commit": "abc123", "version": "0.2.0"},
            "target": {"fixture_commit": "fixture123"},
            "runtime": {
                "claude_code_version": "2.1.269", "model": "claude-sonnet-pinned",
                "judge_model": None, "disable_background_tasks": True,
                "permissions": ["Bash", "Write", "Edit", "Agent", "Skill"],
            },
            "protocol": {
                "runs_per_arm": 3, "arm_order": ["control", "treatment"],
                "ablation": "none", "cases": sorted(self.module.REQUIRED_CASES),
            },
            "arms": {
                "control": {"skill": "implement", "native_result": None, "measured_reports": []},
                "treatment": {"skill": "implement-v3", "native_result": None, "measured_reports": []},
            },
        }

    def test_authorized_preflight_passes(self):
        self.assertEqual(self.module.validate(self.manifest()), [])

    def test_placeholder_or_mismatched_authorization_fails(self):
        manifest = self.manifest()
        manifest["authorization"]["text"] = "Authorize something else"
        manifest["harness"]["commit"] = "replace-with-tested-commit"
        errors = self.module.validate(manifest)
        self.assertTrue(any("authorization text" in item for item in errors))
        self.assertTrue(any("harness.commit" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
