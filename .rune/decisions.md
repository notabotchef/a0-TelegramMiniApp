# Architecture Decisions

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| — | — | — | — |
| 2026-04-13 | Socket.IO: use `/ws` namespace, not root | A0 registers all real-time state on `/ws`; root namespace has no state_push handler | Active |
| 2026-04-13 | WS handler pattern: separate ws_miniapp.py in api/ subdir | Keeps WS logic isolated from REST handlers; matches A0 plugin file routing convention | Active |
| 2026-04-13 | Auth in socket: pass api_key in socket.io auth object | Bearer token not supported on WS; A0 expects api_key in the socket handshake auth payload | Active |
| 2026-04-13 | _get_mcp_token() source: helpers.settings.create_auth_token() | Original call site was broken; helpers.settings is the correct module for token creation in A0 | Active |
