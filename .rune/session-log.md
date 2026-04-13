# Session Log

## 2026-04-12
- Initial onboard. Scanned `Reference/hermes-telegram-miniapp/`. Tech stack: Vanilla JS single-file SPA, no build, Telegram Mini App SDK.

## 2026-04-13
### Fixes Applied
1. **auth.py — _get_mcp_token()**: Was calling a non-existent or wrong function. Fixed to call `create_auth_token()` imported from `helpers.settings`. File: `a0-plugin/_miniapp/api/auth.py`.
2. **Socket.IO namespace**: Discovered A0 uses `/ws` namespace (not root `/`). All prior socket work targeting root namespace was wrong.
3. **Event name**: A0 emits `state_push` events (not `agent_thought`, `tool_call`, etc. as initially assumed).
4. **ws_miniapp.py — new file**: Created `a0-plugin/_miniapp/api/ws_miniapp.py` as a dedicated WS handler. Key config: `requires_api_key=True`, CSRF disabled. Handles `state_request` and `state_push` events.
5. **index.html — connectSocket rewrite**: Now connects with `io(baseUrl + '/ws', { auth: { handlers: ['plugins/_miniapp/ws_miniapp'], api_key: apiKey } })`.

### Live Deployment Path
All changes mirrored to: `/Users/estebannunez/agent-zero/agent-zero/usr/plugins/_miniapp/`

### Blocker
Feed tab connects successfully (receives "Connected to Agent Zero" confirmation) but `state_push` events do not arrive. Root cause unknown — candidates:
- ws_miniapp.py handler not activating (plugin loader may not scan `api/` subdirectory)
- `state_request` emit format incorrect (wrong schema or missing fields)
- A0 actual event name on `/ws` namespace differs from `state_push`
