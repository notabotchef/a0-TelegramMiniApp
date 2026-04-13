"""
POST /api/plugins/_miniapp/contexts_list
Returns list of saved context/chat files from A0's memory.
Requires API key authentication (X-API-KEY header).

Input  (JSON body): {} (no parameters required)
Output 200: { "ok": true, "contexts": [ { "id": "...", "title": "...", "active": true }, ... ] }
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

# Requires API key — not a public endpoint
skip_auth = False
skip_csrf = True


async def execute(request: Any, context: Any = None) -> Any:
    """
    Handle POST /api/plugins/_miniapp/contexts_list.

    Returns all known chat contexts: active in-memory + persisted on disk.
    """
    contexts = []

    # Strategy 1: get active in-memory contexts via AgentContext
    try:
        from python.helpers.agent_context import AgentContext
        for ctx in AgentContext.get_all():
            contexts.append({
                "id": ctx.id,
                "title": f"Context {ctx.id[:8]}",
                "active": True,
            })
    except Exception:
        pass

    # Strategy 2: scan chats directory for persisted context files
    try:
        from python.helpers import files
        chats_dir = files.get_abs_path("memory/chats")
        if os.path.isdir(chats_dir):
            seen = {c["id"] for c in contexts}
            for p in sorted(Path(chats_dir).iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                if p.suffix == ".json":
                    try:
                        with open(p) as f:
                            data = json.load(f)
                        if not isinstance(data, dict):
                            # array/string payload — use filename as id
                            cid = p.stem
                            if cid not in seen:
                                contexts.append({
                                    "id": cid,
                                    "title": f"Chat {cid[:8]}",
                                    "active": False,
                                })
                                seen.add(cid)
                            continue
                        cid = data.get("id") or data.get("ctxid") or p.stem
                        if cid not in seen:
                            contexts.append({
                                "id": cid,
                                "title": data.get("title") or f"Chat {str(cid)[:8]}",
                                "active": False,
                            })
                            seen.add(cid)
                    except Exception:
                        pass
    except Exception:
        pass

    # Strategy 3: scan work_dir for context-like JSON files
    try:
        from python.helpers import files
        workdir = files.get_abs_path("work_dir")
        if os.path.isdir(workdir):
            seen = {c["id"] for c in contexts}
            for p in Path(workdir).glob("*.json"):
                try:
                    with open(p) as f:
                        data = json.load(f)
                    if isinstance(data, dict) and ("id" in data or "ctxid" in data):
                        cid = data.get("id") or data.get("ctxid") or p.stem
                        if cid not in seen:
                            contexts.append({
                                "id": cid,
                                "title": data.get("title") or f"Chat {str(cid)[:8]}",
                                "active": False,
                            })
                            seen.add(cid)
                except Exception:
                    pass
    except Exception:
        pass

    return _json_response({"ok": True, "contexts": contexts}, 200)


def _json_response(data: dict, status: int = 200) -> Any:
    """
    Return a JSON response. Works whether A0 expects a Flask Response
    or a plain (body, status) tuple.
    """
    try:
        from flask import jsonify
        resp = jsonify(data)
        resp.status_code = status
        return resp
    except Exception:
        return json.dumps(data), status
