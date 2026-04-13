"""
POST /api/plugins/_miniapp/shell
Requires X-API-KEY authentication.

Input  (JSON body): { "cmd": str }
Output 200: { "stdout": str, "stderr": str, "exit_code": int, "duration_ms": int }
Output 400: { "error": "cmd is required" }
Output 403: { "error": "Command blocked for safety" }
Output 408: { "error": "Command timed out after Ns" }
Output 500: { "error": "Shell not available. Check Docker setup." }

Blocked commands: rm -rf /, fork bombs, mkfs, dd if=, shutdown, reboot, halt, poweroff.
Timeout and output cap are read from plugin config at request time.
"""

import json
import os
import re
import subprocess
import time

from helpers.api import ApiHandler, Input, Request, Response, Output


_BLOCKLIST_RE = [re.compile(p, re.IGNORECASE) for p in [
    r'rm\s+-rf\s+/\s*$',
    r'rm\s+-rf\s+/\*',
    r':\(\)\s*\{',
    r'\bmkfs\b',
    r'\bdd\s+if\s*=',
    r'>\s*/dev/sd',
    r'\bshutdown\b',
    r'\breboot\b',
    r'\bhalt\b',
    r'\bpoweroff\b',
    r'\binit\s+[06]\b',
]]

_DEFAULT_TIMEOUT    = 30
_DEFAULT_MAX_OUTPUT = 50_000


def _is_blocked(cmd: str) -> bool:
    return any(p.search(cmd) for p in _BLOCKLIST_RE)


def _get_limits() -> tuple[int, int]:
    try:
        from python.helpers import settings as s
        cfg = s.get_settings().get("plugins", {}).get("_miniapp", {})
        return (
            int(cfg.get("shell_timeout",    _DEFAULT_TIMEOUT)),
            int(cfg.get("shell_max_output", _DEFAULT_MAX_OUTPUT)),
        )
    except Exception:
        return _DEFAULT_TIMEOUT, _DEFAULT_MAX_OUTPUT


class Shell(ApiHandler):

    @classmethod
    def requires_api_key(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    async def process(self, input: Input, request: Request) -> Output:
        cmd: str = (input or {}).get("cmd", "").strip()
        if not cmd:
            return Response(
                response=json.dumps({"error": "cmd is required"}),
                status=400, mimetype="application/json")

        if _is_blocked(cmd):
            return Response(
                response=json.dumps({"error": "Command blocked for safety", "exit_code": -1}),
                status=403, mimetype="application/json")

        timeout, max_output = _get_limits()

        start_ms = int(time.time() * 1000)
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True,
                timeout=timeout, cwd="/a0",
                env={**os.environ, "TERM": "xterm"},
            )
        except subprocess.TimeoutExpired:
            return Response(
                response=json.dumps({
                    "error": f"Command timed out after {timeout}s",
                    "exit_code": -1,
                    "duration_ms": int(time.time() * 1000) - start_ms,
                }),
                status=408, mimetype="application/json")
        except FileNotFoundError:
            return Response(
                response=json.dumps({"error": "Shell not available. Check Docker setup."}),
                status=500, mimetype="application/json")
        except Exception as exc:
            return Response(
                response=json.dumps({"error": str(exc), "exit_code": -1}),
                status=500, mimetype="application/json")

        duration_ms = int(time.time() * 1000) - start_ms
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")

        combined = len(stdout) + len(stderr)
        if combined > max_output:
            overflow = combined - max_output
            if len(stderr) >= overflow:
                stderr = stderr[:len(stderr) - overflow] + "\n[output truncated]"
            else:
                stdout = stdout[:max_output - len(stderr)] + "\n[output truncated]"

        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": result.returncode,
            "duration_ms": duration_ms,
        }
