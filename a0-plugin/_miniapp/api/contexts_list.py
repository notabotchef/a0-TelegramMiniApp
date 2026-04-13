"""
POST /api/plugins/_miniapp/contexts_list
Returns list of saved chat contexts from A0's usr/chats/ directory.
Requires API key authentication (X-API-KEY header).

A0 stores chats as: usr/chats/<id>/chat.json
  { "id": "RYj73pK1", "name": "Chat title", "created_at": "...", ... }

Input  (JSON body): {} (no parameters required)
Output 200: { "ok": true, "contexts": [ { "id": "...", "title": "...", "active": bool }, ... ] }
"""

import json
import os
from pathlib import Path
from typing import Any

# Requires API key — not a public endpoint
skip_auth = False
skip_csrf = True


async def execute(request: Any, context: Any = None) -> Any:
    contexts = []
    seen: set = set()

    # Strategy 1: active in-memory contexts via AgentContext
    try:
        from python.helpers.agent_context import AgentContext
        for ctx in AgentContext.get_all():
            contexts.append({
                "id":     ctx.id,
                "title":  getattr(ctx, "name", None) or f"Chat {ctx.id[:8]}",
                "active": True,
            })
            seen.add(ctx.id)
    except Exception:
        pass

    # Strategy 2: persisted chats — usr/chats/<id>/chat.json
    # Each subdirectory is one chat; the JSON has keys: id, name, created_at, ...
    try:
        from python.helpers import files
        chats_dir = files.get_abs_path("usr/chats")
        if os.path.isdir(chats_dir):
            entries = sorted(
                Path(chats_dir).iterdir(),
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )
            for entry in entries:
                chat_file = entry / "chat.json"
                if not (entry.is_dir() and chat_file.exists()):
                    continue
                try:
                    with open(chat_file) as f:
                        data = json.load(f)
                    if not isinstance(data, dict):
                        # unexpected format — use dir name as id
                        cid = entry.name
                        if cid not in seen:
                            contexts.append({
                                "id":     cid,
                                "title":  f"Chat {cid[:8]}",
                                "active": False,
                            })
                            seen.add(cid)
                        continue
                    cid = data.get("id") or entry.name
                    if cid not in seen:
                        contexts.append({
                            "id":     cid,
                            "title":  data.get("name") or data.get("title") or f"Chat {str(cid)[:8]}",
                            "active": False,
                        })
                        seen.add(cid)
                except Exception:
                    pass
    except Exception:
        pass

    return _json_response({"ok": True, "contexts": contexts}, 200)


def _json_response(data: dict, status: int = 200) -> Any:
    try:
        from flask import jsonify
        resp = jsonify(data)
        resp.status_code = status
        return resp
    except Exception:
        return json.dumps(data), status
