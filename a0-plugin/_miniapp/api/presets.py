"""
GET /api/plugins/_miniapp/presets
Returns model presets from _model_config/presets.yaml.
Requires X-API-KEY.
"""
import json
from helpers.api import ApiHandler, Request, Response


class Presets(ApiHandler):
    @classmethod
    def requires_api_key(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_methods(cls):
        return ["GET", "POST"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        try:
            import yaml
            from helpers import files

            presets_path = files.get_abs_path(
                "usr/plugins/_model_config/presets.yaml"
            )
            with open(presets_path) as f:
                presets = yaml.safe_load(f)
            return {"ok": True, "presets": presets or []}
        except Exception:
            return {"ok": True, "presets": []}
