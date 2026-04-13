"""
WebSocket handler for the Telegram mini app.
Authenticated via api_key (no session/CSRF required).
Path for auth.handlers: "plugins/_miniapp/ws_miniapp"
"""

from helpers.ws import WsHandler
from helpers import extension


class WsMiniapp(WsHandler):

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return True

    async def on_connect(self, sid: str) -> None:
        await extension.call_extensions_async(
            "webui_ws_connect", agent=None, instance=self, sid=sid
        )

    async def on_disconnect(self, sid: str) -> None:
        await extension.call_extensions_async(
            "webui_ws_disconnect", agent=None, instance=self, sid=sid
        )

    async def process(self, event: str, data: dict, sid: str) -> dict | None:
        response_data: dict = {}
        await extension.call_extensions_async(
            "webui_ws_event",
            agent=None,
            instance=self,
            sid=sid,
            event_type=event,
            data=data,
            response_data=response_data,
        )
        return response_data if response_data else None
