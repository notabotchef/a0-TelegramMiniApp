"""
POST /api/plugins/_miniapp/reset
Resets the agent cache (equivalent to cache_reset from loopback).
Requires X-API-KEY.
"""
from helpers.api import ApiHandler, Request, Response


class Reset(ApiHandler):
    @classmethod
    def requires_api_key(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls):
        return ["POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            from helpers import cache
            cache.clear_all()
            return {"ok": True, "message": "Agent cache reset."}
        except Exception as e:
            return Response(
                response='{"error": "Reset failed"}',
                status=500,
                mimetype="application/json",
            )
