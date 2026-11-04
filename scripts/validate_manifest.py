#!/usr/bin/env python3
"""Validate the unchanged fixtures against vendored official 1.0.0 schemas."""

import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator


def main():
    root = Path(__file__).resolve().parents[1]
    checks = []
    for component in ("plugin", "mcp"):
        relative = f"plugins/canary-plugin/{component}.json"
        schema_path = root / f"schemas/1.0.0/{component}.schema.json"
        schema_bytes = schema_path.read_bytes()
        schema = json.loads(schema_bytes)
        Draft202012Validator.check_schema(schema)
        errors = list(Draft202012Validator(schema).iter_errors(json.loads((root / relative).read_text())))
        checks.append({
            "file": relative,
            "schema_url": schema["$id"],
            "schema_sha256": hashlib.sha256(schema_bytes).hexdigest(),
            "result": "PASS" if not errors else "FAIL",
            "errors": [error.message for error in errors],
        })
    report = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "validator": f"jsonschema {importlib.metadata.version('jsonschema')} / Draft 2020-12",
        "checks": checks,
    }
    output = root / "results/schema-validation.json"
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if all(check["result"] == "PASS" for check in checks) else 1)


if __name__ == "__main__":
    main()
