"""
POST /api/plugins/_miniapp/shell
Requires X-API-KEY authentication (enforced by A0 framework — skip_auth NOT set).

Input  (JSON body): { "cmd": str }
Output 200: { "stdout": str, "stderr": str, "exit_code": int, "duration_ms": int }
Output 400: { "error": "cmd is required" }
Output 403: { "error": "Command blocked for safety" }
Output 408: { "error": "Command timed out after 30s" }
Output 500: { "error": "Shell not available. Check Docker setup." }

Safety: blocklist of destructive commands.
Output capped at 50 000 chars combined.
"""

import json
import os
import re
import subprocess
import time
from typing import Any

# Regex patterns that must not match the command (case-insensitive)
# Each entry is a compiled regex applied to the lowercased command.
_BLOCKLIST_RE = [re.compile(p, re.IGNORECASE) for p in [
    r'rm\s+-rf\s+/\s*$',           # rm -rf /   (root only, not subdirs)
    r'rm\s+-rf\s+/\*',             # rm -rf /*
    r':\(\)\s*\{',                  # fork bomb: :(){
    r'\bmkfs\b',
    r'\bdd\s+if\s*=',
    r'>\s*/dev/sd',
    r'\bshutdown\b',
    r'\breboot\b',
    r'\bhalt\b',
    r'\bpoweroff\b',
    r'\binit\s+[06]\b',
]]

_MAX_OUTPUT = 50_000   # chars (default — overridden by plugin config)
_TIMEOUT    = 30       # seconds (default — overridden by plugin config)


def _get_plugin_config() -> dict:
    """Read _miniapp plugin config from A0 settings. Returns {} on any failure."""
    try:
        from python.helpers import settings as s
        cfg = s.get_settings()
        return cfg.get("plugins", {}).get("_miniapp", {})
    except Exception:
        return {}


def _is_blocked(cmd: str) -> bool:
    return any(p.search(cmd) for p in _BLOCKLIST_RE)


def _json_response(data: dict, status: int = 200) -> Any:
    try:
        from flask import jsonify
        resp = jsonify(data)
        resp.status_code = status
        return resp
    except Exception:
        return json.dumps(data), status


async def execute(request: Any, context: Any = None) -> Any:
    """Handle POST /api/plugins/_miniapp/shell."""
    # --- Parse body ---
    body: dict = {}
    try:
        if hasattr(request, "get_json"):
            body = request.get_json(force=True, silent=True) or {}
        elif hasattr(request, "json"):
            body = request.json or {}
        elif isinstance(request, dict):
            body = request
    except Exception:
        pass

    cmd: str = body.get("cmd", "").strip()
    if not cmd:
        return _json_response({"error": "cmd is required"}, 400)

    if _is_blocked(cmd):
        return _json_response({"error": "Command blocked for safety", "exit_code": -1}, 403)

    # --- Read limits from plugin config (fall back to module defaults) ---
    plugin_cfg = _get_plugin_config()
    timeout    = int(plugin_cfg.get("shell_timeout",    _TIMEOUT))
    max_output = int(plugin_cfg.get("shell_max_output", _MAX_OUTPUT))

    # --- Run subprocess ---
    start_ms = int(time.time() * 1000)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=timeout,
            cwd="/a0",
            env={**os.environ, "TERM": "xterm"},
        )
    except subprocess.TimeoutExpired:
        duration_ms = int(time.time() * 1000) - start_ms
        return _json_response(
            {"error": f"Command timed out after {timeout}s", "exit_code": -1, "duration_ms": duration_ms},
            408,
        )
    except FileNotFoundError:
        return _json_response({"error": "Shell not available. Check Docker setup."}, 500)
    except Exception as exc:
        return _json_response({"error": str(exc), "exit_code": -1}, 500)

    duration_ms = int(time.time() * 1000) - start_ms

    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")

    # Cap combined output to configured limit
    combined = len(stdout) + len(stderr)
    if combined > max_output:
        overflow = combined - max_output
        if len(stderr) >= overflow:
            stderr = stderr[: len(stderr) - overflow] + "\n[output truncated]"
        else:
            remaining = max_output - len(stderr)
            stdout = stdout[:remaining] + "\n[output truncated]"

    return _json_response(
        {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.returncode,
            "duration_ms": duration_ms,
        },
        200,
    )
