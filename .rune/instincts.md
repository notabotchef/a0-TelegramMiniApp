# Project Instincts

Learned trigger→action patterns. Managed by session-bridge. See session-bridge SKILL.md Step 5.7 for format.

## A0 Plugin Patterns

**TRIGGER**: Socket.IO not receiving events despite successful connect
**ACTION**: Check (1) namespace — A0 uses `/ws` not root; (2) event name — use `state_push` not `agent_thought`; (3) handler activation — verify plugin loader picks up the handler file path

**TRIGGER**: Auth fails in A0 plugin Python code
**ACTION**: Token creation lives in `helpers.settings.create_auth_token()` — import from there, not from auth module directly

**TRIGGER**: New WS handler needed for A0 plugin
**ACTION**: Create file in `_miniapp/api/ws_miniapp.py`, set `requires_api_key=True`, disable CSRF, handle both `state_request` (client→server) and `state_push` (server→client) events

**TRIGGER**: Deploying miniapp changes during development
**ACTION**: Mirror all changes to live A0 path: `/Users/estebannunez/agent-zero/agent-zero/usr/plugins/_miniapp/`
