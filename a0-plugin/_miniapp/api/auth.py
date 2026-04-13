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


def _get_telegram_config() -> tuple[list[str], list[int]]:
    """
    Return (bot_tokens, allowed_user_ids) from _telegram_integration plugin config.
    bot_tokens: all enabled bot tokens (try each during validation).
    allowed_user_ids: union of allowed_users across all enabled bots; empty = allow all.
    """
    bot_tokens: list[str] = []
    allowed_ids: set[int] = set()
    try:
        from python.helpers import settings as s
        cfg = s.get_settings()
        plugins_cfg = cfg.get("plugins", {})
        tg = plugins_cfg.get("_telegram_integration", {})
        bots = tg.get("bots", [])
        for bot in bots:
            if not bot.get("enabled", True):
                continue
            token = bot.get("token", "").strip()
            if token:
                bot_tokens.append(token)
            for uid in bot.get("allowed_users", []):
                try:
                    allowed_ids.add(int(uid))
                except (ValueError, TypeError):
                    pass
    except Exception:
        pass
    return bot_tokens, list(allowed_ids)


def _get_plugin_config() -> dict:
    """Read _miniapp plugin config from A0 settings. Returns {} on any failure."""
    try:
        from python.helpers import settings as s
        cfg = s.get_settings()
        return cfg.get("plugins", {}).get("_miniapp", {})
    except Exception:
        return {}


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


def _extract_user_id(init_data: str) -> Optional[int]:
    """Extract user.id from the 'user' field of initData. Returns None on any failure."""
    try:
        parsed = urllib.parse.parse_qs(init_data, keep_blank_values=True)
        user_json = parsed.get("user", [None])[0]
        if user_json:
            user = json.loads(user_json)
            return int(user["id"])
    except Exception:
        pass
    return None


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

    # --- Read plugin config to check require_auth ---
    plugin_cfg  = _get_plugin_config()
    require_auth = plugin_cfg.get("require_auth", True)

    if require_auth:
        if not init_data:
            return _json_response({"error": "init_data is required"}, 400)

        # --- Get all bot tokens + allowed users ---
        bot_tokens, allowed_user_ids = _get_telegram_config()
        if not bot_tokens:
            return _json_response(
                {"error": "Telegram plugin not found. Enable it in Agent Zero settings."},
                503,
            )

        # --- Validate initData HMAC against all configured bot tokens ---
        valid = any(_validate_init_data(init_data, tok) for tok in bot_tokens)
        if not valid:
            return _json_response({"error": "invalid signature"}, 401)

        # --- Authorize Telegram user against allowed_users ---
        if allowed_user_ids:
            telegram_user_id = _extract_user_id(init_data)
            if telegram_user_id is None or telegram_user_id not in allowed_user_ids:
                return _json_response({"error": "user not authorized"}, 403)
    # require_auth=false: skip initData check, issue api_key directly.
    # Caller must still present X-API-KEY on subsequent requests.

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
