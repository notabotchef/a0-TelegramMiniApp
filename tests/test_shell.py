"""
Unit tests for a0-plugin/_miniapp/api/shell.py

Run with:
    python -m pytest tests/test_shell.py -v

Execute tests that run subprocesses are skipped outside a Docker container
(they require /a0 to exist).
"""

import sys
import os
import asyncio
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'a0-plugin', '_miniapp', 'api'))

from shell import _is_blocked, execute  # noqa: E402

# Execute tests require /a0 to exist (inside Docker container)
requires_docker = pytest.mark.skipif(
    not os.path.isdir('/a0'),
    reason="requires Docker container with /a0 directory",
)


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _parse(result):
    """Normalise (body, status) tuple or Flask Response into (dict, int)."""
    if isinstance(result, tuple):
        body, status = result
        data = json.loads(body) if isinstance(body, str) else body
        return data, status
    return result.get_json(), result.status_code


# ─── BLOCKLIST TESTS ─────────────────────────────────────────────────────────

class TestBlocklist:

    def test_rm_rf_root_blocked(self):
        assert _is_blocked('rm -rf /') is True

    def test_rm_rf_root_trailing_space_blocked(self):
        assert _is_blocked('rm -rf /  ') is True

    def test_rm_rf_root_wildcard_blocked(self):
        assert _is_blocked('rm -rf /*') is True

    def test_rm_subdir_not_blocked(self):
        """rm -rf on a subdirectory must NOT be blocked."""
        assert _is_blocked('rm -rf /tmp/mydir') is False

    def test_rm_var_not_blocked(self):
        assert _is_blocked('rm -rf /var/cache/apt') is False

    def test_fork_bomb_blocked(self):
        assert _is_blocked(':(){ :|:& };:') is True

    def test_mkfs_blocked(self):
        assert _is_blocked('mkfs.ext4 /dev/sda') is True

    def test_dd_blocked(self):
        assert _is_blocked('dd if=/dev/zero of=/dev/sda') is True

    def test_shutdown_blocked(self):
        assert _is_blocked('shutdown -h now') is True

    def test_reboot_blocked(self):
        assert _is_blocked('reboot') is True

    def test_halt_blocked(self):
        assert _is_blocked('halt') is True

    def test_poweroff_blocked(self):
        assert _is_blocked('poweroff') is True

    def test_safe_ls_not_blocked(self):
        assert _is_blocked('ls -la') is False

    def test_echo_not_blocked(self):
        assert _is_blocked('echo hello') is False

    def test_python_version_not_blocked(self):
        assert _is_blocked('python3 --version') is False

    def test_case_insensitive_rm(self):
        assert _is_blocked('RM -RF /') is True

    def test_case_insensitive_shutdown(self):
        assert _is_blocked('SHUTDOWN -h now') is True


# ─── EXECUTE TESTS ────────────────────────────────────────────────────────────

class TestExecute:

    def test_missing_cmd_returns_400(self):
        data, status = _parse(_run(execute({})))
        assert status == 400
        assert 'error' in data

    def test_empty_cmd_returns_400(self):
        data, status = _parse(_run(execute({'cmd': '   '})))
        assert status == 400

    def test_blocked_cmd_returns_403(self):
        data, status = _parse(_run(execute({'cmd': 'rm -rf /'})))
        assert status == 403
        assert 'blocked' in data['error'].lower()

    def test_blocked_fork_bomb_returns_403(self):
        data, status = _parse(_run(execute({'cmd': ':(){ :|:& };:'})))
        assert status == 403

    @requires_docker
    def test_echo_command_returns_output(self):
        data, status = _parse(_run(execute({'cmd': 'echo hello_world'})))
        assert status == 200
        assert 'hello_world' in data.get('stdout', '')
        assert data.get('exit_code') == 0

    @requires_docker
    def test_duration_ms_present(self):
        data, status = _parse(_run(execute({'cmd': 'echo test'})))
        assert status == 200
        assert 'duration_ms' in data
        assert isinstance(data['duration_ms'], int)
        assert data['duration_ms'] >= 0

    @requires_docker
    def test_nonzero_exit_code_returned(self):
        data, status = _parse(_run(execute({'cmd': 'exit 42'})))
        assert status == 200
        assert data.get('exit_code') == 42
