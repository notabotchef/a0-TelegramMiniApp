"""
POST /api/plugins/_miniapp/auth
No authentication required — this IS the authentication endpoint.

Input  (JSON body): { "init_data": "<Telegram WebApp.initData string>" }
Output 200: { "api_key": "<mcp_server_token>" }
Output 401: { "error": "invalid signature" }
Output 503: { "error": "Telegram plugin not found. Enable it in Agent Zero settings." }
Output 500: { "error": "Agent Zero API key not configured. Set it in A0 settings." }
"""

import hmac
import hashlib
import json
import urllib.parse
from typing import Optional

from helpers.api import ApiHandler, Input, Request, Response, Output


def _get_telegram_config() -> tuple[list[str], list[int]]:
    bot_tokens: list[str] = []
    allowed_ids: set[int] = set()
    try:
        import json
        from helpers import files
        cfg_path = files.get_abs_path("usr/plugins/_telegram_integration/config.json")
        with open(cfg_path) as f:
            tg = json.load(f)
        for bot in tg.get("bots", []):
            if not bot.get("enabled", True):
                continue
            token = bot.get("token", "").strip()
            if token:
                bot_tokens.append(token)
            for uid in bot.get("allowed_users", []):
                # allowed_users can be "123456" strings or "@username" — skip usernames
                try:
                    allowed_ids.add(int(str(uid).strip()))
                except (ValueError, TypeError):
                    pass
    except Exception:
        pass
    return bot_tokens, list(allowed_ids)


def _get_plugin_config() -> dict:
    try:
        from python.helpers import settings as s
        return s.get_settings().get("plugins", {}).get("_miniapp", {})
    except Exception:
        return {}


def _get_mcp_token() -> Optional[str]:
    try:
        from helpers.settings import create_auth_token
        return create_auth_token()
    except Exception:
        return None


def _validate_init_data(init_data: str, bot_token: str) -> bool:
    try:
        parsed = urllib.parse.parse_qs(init_data, keep_blank_values=True)
        fields = {k: v[0] for k, v in parsed.items()}
        hash_value = fields.pop("hash", None)
        if not hash_value:
            return False
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, hash_value)
    except Exception:
        return False


def _extract_user_id(init_data: str) -> Optional[int]:
    try:
        parsed = urllib.parse.parse_qs(init_data, keep_blank_values=True)
        user_json = parsed.get("user", [None])[0]
        if user_json:
            return int(json.loads(user_json)["id"])
    except Exception:
        pass
    return None


class Auth(ApiHandler):

    @classmethod
    def requires_auth(cls) -> bool:
        return False  # this IS the auth endpoint

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False

    async def process(self, input: Input, request: Request) -> Output:
        plugin_cfg   = _get_plugin_config()
        require_auth = plugin_cfg.get("require_auth", True)

        if require_auth:
            init_data: str = (input or {}).get("init_data", "")
            if not init_data:
                return Response(
                    response=json.dumps({"error": "init_data is required"}),
                    status=400, mimetype="application/json")

            bot_tokens, allowed_user_ids = _get_telegram_config()
            if not bot_tokens:
                return Response(
                    response=json.dumps({"error": "Telegram plugin not found. Enable it in Agent Zero settings."}),
                    status=503, mimetype="application/json")

            if not any(_validate_init_data(init_data, tok) for tok in bot_tokens):
                return Response(
                    response=json.dumps({"error": "invalid signature"}),
                    status=401, mimetype="application/json")

            if allowed_user_ids:
                uid = _extract_user_id(init_data)
                if uid is None or uid not in allowed_user_ids:
                    return Response(
                        response=json.dumps({"error": "user not authorized"}),
                        status=403, mimetype="application/json")

        mcp_token = _get_mcp_token()
        if not mcp_token:
            return Response(
                response=json.dumps({"error": "Agent Zero API key not configured. Set it in A0 settings."}),
                status=500, mimetype="application/json")

        return {"api_key": mcp_token}
