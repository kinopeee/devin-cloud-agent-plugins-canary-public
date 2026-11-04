import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/canary-plugin"
SPEC = importlib.util.spec_from_file_location("canary_server", PLUGIN / "canary_server.py")
SERVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SERVER)


class CanaryTests(unittest.TestCase):
    def test_minimal_manifest_and_skill(self):
        manifest = json.loads((PLUGIN / "plugin.json").read_text())
        self.assertEqual(set(manifest), {"$schema", "name"})
        skill_lines = (PLUGIN / "skills/canary/SKILL.md").read_text().splitlines()
        self.assertEqual(skill_lines[0], "---")
        self.assertEqual(skill_lines[-1], "---")
        self.assertEqual(len(skill_lines), 4)

    def test_stdio_protocol_and_actual_environment(self):
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "canary_env", "arguments": {}}},
        ]
        env = {key: value for key, value in os.environ.items() if key not in ("PLUGIN_ROOT", "PLUGIN_DATA")}
        result = subprocess.run(
            [sys.executable, str(PLUGIN / "canary_server.py")],
            input="".join(json.dumps(message) + "\n" for message in messages),
            text=True, capture_output=True, check=True, timeout=10, env=env,
        )
        replies = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(replies), 3)
        self.assertEqual(replies[0]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(replies[1]["result"]["tools"][0]["name"], "canary_env")
        values = json.loads(replies[2]["result"]["content"][0]["text"])
        self.assertEqual(values, {"PLUGIN_ROOT": None, "PLUGIN_DATA": None})
        self.assertEqual(result.stderr, "")

    def test_unknown_method(self):
        response = SERVER.handle({"jsonrpc": "2.0", "id": 4, "method": "not_a_method"})
        self.assertEqual(response["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
