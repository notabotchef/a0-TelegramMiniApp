# Master Plan: Agent Zero Telegram Mini App v0.1

## What This Is
Control panel + power tools for Agent Zero, living inside Telegram.
NOT a chat interface — you already chat via the Telegram bot.
Single-file SPA (`index.html`). No build step.

## Key Decisions
- **initData-only auth** — everyone using this has Telegram. No API key typing. Telegram identity = auth.
- **miniapp_auth plugin** — one `.py` file we ship that drops into A0's plugin directory, validates initData HMAC-SHA256 using the stored bot token, returns the MCP server token.
- **No fallback to API key** — if Telegram plugin not active, show clear error instructing user to enable it.
- **Socket.IO for activity feed** — real-time tool calls, thoughts, steps as A0 works.
- **Direct shell via plugin** — `shell.py` in miniapp plugin. Subprocess with output streaming via Socket.IO.
- **Tunnel widget** — display A0's built-in tunnel URL, start/stop from Mini App.
- **4 tabs** — Feed, Config, Manage, Shell. No chat tab.
- **Agent Zero palette** — #0d0d0d bg, #22c55e green accent, Telegram theme vars.
- **PR-gated** — all code on feature branches, PR required before merging to main.
- **rune:cook** for any task > 20 LOC.

## Architecture
```
Telegram Client (WebView)
  └─ index.html (~90KB single file)
       ├─ Telegram WebApp SDK (CDN, initData auth)
       ├─ Socket.IO 4.7.5 (CDN, real-time feed)
       └─ HTTPS → Agent Zero (Docker :50080)
            ├─ POST /api/plugins/_miniapp/auth          ← NEW (we ship this)
            ├─ POST /api/plugins/_miniapp/shell         ← NEW (we ship this)
            ├─ GET  /api/health                         (no auth)
            ├─ POST /api/plugins/_model_config/*        (LLM switcher)
            ├─ POST /api/plugins  {action: toggle_plugin}
            ├─ POST /api/plugins_list
            ├─ POST /api/history_get
            ├─ POST /api/chat_create / chat_remove / chat_reset
            ├─ POST /api/scheduler_tasks_list / _run / _delete
            ├─ POST /api/tunnel {action: get/create/stop}
            ├─ POST /api/nudge                          (reset agent)
            └─ Socket.IO /  {auth: {handlers: ['webui']}}
```

## A0 Plugin Files We Ship
```
a0-plugin/
  _miniapp/
    plugin.yaml          ← plugin metadata
    api/
      auth.py            ← validates initData → returns api_key
      shell.py           ← runs subprocess, streams output
    default_config.yaml  ← allowed_users list
```

Mount via docker-compose volume: `./a0-plugin/_miniapp:/a0/usr/plugins/_miniapp`

## 4 Tabs
| Tab | Icon | What it shows |
|-----|------|---------------|
| Feed | ⚡ | Real-time Socket.IO: tool calls, thoughts, steps |
| Config | ⚙️ | LLM model switcher + Plugin toggle cards + Reset |
| Manage | 💬 | Chat list + Scheduler tasks |
| Shell | >_ | Direct shell → subprocess output streaming |

## Phases
| # | Phase | Output | Status |
|---|-------|--------|--------|
| 1 | A0 plugin + scaffold + auth | `_miniapp/` plugin, index.html shell, initData handshake | ✅ Complete |
| 2 | Feed tab | Socket.IO activity stream, tool bubbles, real-time thoughts | ⬚ Pending |
| 3 | Config tab | LLM switcher, plugin toggle cards, reset/nudge | ⬚ Pending |
| 4 | Manage tab | Chat list, scheduler, tunnel widget | ✅ Complete (PR#4 open) |
| 5 | Shell tab + polish + release | Direct shell, keyboard UX, v0.1.0 tag | ✅ Complete (PR#5 open) |

## Risks
- Socket.IO event names from A0 (`agent_response`, `agent_tool`) need verification against live instance before Phase 2
- Shell subprocess in Docker needs PATH set correctly in `shell.py`
- `_model_config` plugin may not be installed on all A0 instances → graceful degraded state
- ALLOWED_ORIGINS must include `https://web.telegram.org` on A0 side

## Workflow
- All code on `feat/<phase-name>` branches
- PR required before merging to `main`  
- rune:cook for any task > 20 LOC
