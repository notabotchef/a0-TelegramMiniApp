"""
POST /api/plugins/_miniapp/auth
No authentication required — this IS the authentication endpoint.

Input  (JSON body): { "init_data": "<Telegram WebApp.initData string>" }
Output 200: { "api_key": "<mcp_server_token>" }
Output 401: { "error": "invalid signature" }
Output 503: { "error": "Telegram plugin not found. Enable it in Agent Zero settings." }
Output 500: { "error": "Agent Zero API key not configured. Set it in A0 settings." }

Validation algorithm (Telegram docs):
  1. Parse init_data: split on '&', extract 'hash' field
  2. Sort remaining fields, join with '\n' → data_check_string
  3. secret_key = HMAC-SHA256(key=b"WebAppData", msg=bot_token_bytes).digest()
  4. expected_hash = HMAC-SHA256(key=secret_key, msg=data_check_string.encode()).hexdigest()
  5. Compare expected_hash == hash (constant-time)
"""

import hmac
import hashlib
import json
import urllib.parse
from typing import Any, Optional

# ── Agent Zero plugin API surface ────────────────────────────────────────────
# A0 calls: result = await execute(agent, ...) for tool-style plugins
# For HTTP endpoint plugins, A0 imports and calls execute(request, context)
# We register as a no-auth endpoint so A0 routes POST /api/plugins/_miniapp/auth here.

# Skip auth + CSRF — this endpoint IS the auth issuer.
skip_auth = True
skip_csrf = True


def _get_bot_token() -> Optional[str]:
    """Retrieve the Telegram bot token from the _telegram_integration plugin config."""
    try:
        # A0 plugin config access pattern (matches how webhook.py does it)
        from python.helpers import settings as s
        cfg = s.get_settings()
        # _telegram_integration stores bots as a list under "bots"
        plugins_cfg = cfg.get("plugins", {})
        tg = plugins_cfg.get("_telegram_integration", {})
        bots = tg.get("bots", [])
        if bots and bots[0].get("token"):
            return bots[0]["token"]
    except Exception:
        pass
    return None


def _get_mcp_token() -> Optional[str]:
    """Retrieve the MCP server token from Agent Zero settings."""
    try:
        from python.helpers import settings as s
        cfg = s.get_settings()
        token = cfg.get("mcp_server_token") or cfg.get("api_key")
        if token:
            return token
    except Exception:
        pass
    return None


def _validate_init_data(init_data: str, bot_token: str) -> bool:
    """
    Validate Telegram WebApp initData HMAC-SHA256 signature.
    Returns True if signature is valid, False otherwise.
    """
    try:
        # Parse the URL-encoded string
        parsed = urllib.parse.parse_qs(init_data, keep_blank_values=True)
        # parse_qs returns lists; flatten to single values
        fields = {k: v[0] for k, v in parsed.items()}

        hash_value = fields.pop("hash", None)
        if not hash_value:
            return False

        # Build data-check string: sorted key=value pairs joined by '\n'
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(fields.items())
        )

        # secret_key = HMAC-SHA256(key="WebAppData", msg=bot_token)
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        # expected_hash = HMAC-SHA256(key=secret_key, msg=data_check_string)
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(expected_hash, hash_value)
    except Exception:
        return False


async def execute(request: Any, context: Any = None) -> Any:
    """
    Handle POST /api/plugins/_miniapp/auth.

    A0's HTTP plugin dispatcher passes the raw request object.
    We support both Flask-style (request.json / request.get_json())
    and dict-style (already-parsed body) callers.
    """
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

    init_data: str = body.get("init_data", "")
    if not init_data:
        return _json_response({"error": "init_data is required"}, 400)

    # --- Get bot token ---
    bot_token = _get_bot_token()
    if not bot_token:
        return _json_response(
            {"error": "Telegram plugin not found. Enable it in Agent Zero settings."},
            503,
        )

    # --- Validate initData ---
    if not _validate_init_data(init_data, bot_token):
        return _json_response({"error": "invalid signature"}, 401)

    # --- Get MCP server token to hand back as api_key ---
    mcp_token = _get_mcp_token()
    if not mcp_token:
        return _json_response(
            {"error": "Agent Zero API key not configured. Set it in A0 settings."},
            500,
        )

    # initData is intentionally NOT stored — discard after validation
    return _json_response({"api_key": mcp_token}, 200)


def _json_response(data: dict, status: int = 200) -> Any:
    """
    Return a JSON response.  Works whether A0 expects a Flask Response
    or a plain (body, status) tuple — try Flask first, fall back to tuple.
    """
    try:
        from flask import jsonify
        resp = jsonify(data)
        resp.status_code = status
        return resp
    except Exception:
        return json.dumps(data), status
