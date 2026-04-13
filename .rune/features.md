# Feature Map

| Feature | Status | Key Files | Dependencies |
|---------|--------|-----------|--------------|
| Auth (initData handshake) | Planned | `a0-plugin/_miniapp/api/auth.py`, `index.html` | Telegram plugin active in A0 |
| Shell plugin | Planned | `a0-plugin/_miniapp/api/shell.py` | Docker subprocess |
| Setup screen (URL only) | Planned | `index.html` | Auth |
| Feed tab (Socket.IO activity) | Planned | `index.html` | Socket.IO, A0 websocket events |
| Config tab (LLM + Plugins + Reset) | Planned | `index.html` | `_model_config` plugin, `/api/plugins` |
| Manage tab (Chats + Scheduler + Tunnel) | Planned | `index.html` | `/api/history_get`, `/api/scheduler_*`, `/api/tunnel` |
| Shell tab | Planned | `index.html`, `shell.py` | Shell plugin |
| Tunnel widget | Planned | `index.html` | `/api/tunnel` |

## Dependency Graph
```
Auth (Phase 1)
  ├─ Feed tab (Phase 2) ← Socket.IO
  ├─ Config tab (Phase 3) ← model_config + plugins API
  ├─ Manage tab (Phase 4) ← chats + scheduler + tunnel API
  └─ Shell tab (Phase 5) ← shell.py plugin
```

## v0.2 Backlog
- Image/file viewer from A0 work directory
- Memory browser (A0 memory system)
- Multiple bot support
- Push notifications for task completion
- Chat creation with profile/project selection
- Log viewer (A0 system logs)
