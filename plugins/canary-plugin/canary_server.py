#!/usr/bin/env python3
"""Dependency-free stdio MCP canary; returns only two plugin environment values."""

import json
import os
import sys


def handle(request):
    if "id" not in request:
        return None
    method = request.get("method")
    params = request.get("params", {})
    if method == "initialize":
        result = {
            "protocolVersion": params.get("protocolVersion", "2024-11-05"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "canary-env", "version": "1.0.0"},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {
            "tools": [{
                "name": "canary_env",
                "description": "Return the actual PLUGIN_ROOT and PLUGIN_DATA environment values.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            }]
        }
    elif method == "tools/call" and params.get("name") == "canary_env":
        values = {name: os.environ.get(name) for name in ("PLUGIN_ROOT", "PLUGIN_DATA")}
        result = {"content": [{"type": "text", "text": json.dumps(values)}], "isError": False}
    else:
        return {
            "jsonrpc": "2.0",
            "id": request["id"],
            "error": {"code": -32601, "message": "Method or tool not found"},
        }
    return {"jsonrpc": "2.0", "id": request["id"], "result": result}


def main():
    for line in sys.stdin:
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        else:
            response = handle(request)
        if response is not None:
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
