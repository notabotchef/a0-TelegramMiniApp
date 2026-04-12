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
import subprocess
import time
from typing import Any

# Patterns that must not appear in submitted commands (substring match, case-insensitive)
_BLOCKLIST = [
    "rm -rf /",
    "rm -rf /*",
    ":(){ :|:& };:",          # fork bomb
    "mkfs",
    "dd if=",
    "dd if =",
    "> /dev/sd",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "init 0",
    "init 6",
]

_MAX_OUTPUT = 50_000   # chars
_TIMEOUT    = 30       # seconds


def _is_blocked(cmd: str) -> bool:
    low = cmd.lower()
    return any(pattern.lower() in low for pattern in _BLOCKLIST)


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

    # --- Run subprocess ---
    start_ms = int(time.time() * 1000)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            timeout=_TIMEOUT,
            cwd="/a0",
            env={**os.environ, "TERM": "xterm"},
        )
    except subprocess.TimeoutExpired:
        duration_ms = int(time.time() * 1000) - start_ms
        return _json_response(
            {"error": f"Command timed out after {_TIMEOUT}s", "exit_code": -1, "duration_ms": duration_ms},
            408,
        )
    except FileNotFoundError:
        return _json_response({"error": "Shell not available. Check Docker setup."}, 500)
    except Exception as exc:
        return _json_response({"error": str(exc), "exit_code": -1}, 500)

    duration_ms = int(time.time() * 1000) - start_ms

    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")

    # Cap combined output
    combined = len(stdout) + len(stderr)
    if combined > _MAX_OUTPUT:
        overflow = combined - _MAX_OUTPUT
        if len(stderr) >= overflow:
            stderr = stderr[: len(stderr) - overflow] + "\n[output truncated]"
        else:
            remaining = _MAX_OUTPUT - len(stderr)
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
