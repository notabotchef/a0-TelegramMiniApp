# Agent0TelegramApp — Project Configuration

## Overview
Telegram Mini App for Agent Zero — a terminal-style chat interface running inside Telegram. Connects to a local agent gateway via SSE streaming and REST. Reference implementation: `Reference/hermes-telegram-miniapp/` (hermes-telegram-miniapp, MIT).

## Tech Stack
- Framework: Telegram Mini App (WebApp SDK)
- Language: JavaScript (Vanilla) + HTML + CSS
- Package Manager: none (no build step)
- Test Framework: none
- Build Tool: none
- Linter: none

## Directory Structure
```
Agent0TelegramApp/
├── _miniapp/                      # A0 plugin (drop into usr/plugins/)
│   ├── plugin.yaml                # Plugin metadata
│   ├── default_config.yaml        # Shell timeout, auth settings
│   ├── api/                       # Backend API handlers
│   └── webui/                     # Frontend (index.html + config.html)
├── index.html                     # Standalone SPA (dev/reference)
├── index.yaml                     # a0-plugins registry entry
├── Screenshots/                   # App screenshots + thumbnail
└── Reference/                     # Original hermes-telegram-miniapp
```

## Conventions (from reference implementation)
- **Naming**: camelCase for JS functions/vars; kebab-case for CSS classes and HTML IDs
- **Architecture**: Single-file SPA — all HTML, CSS, JS in one `index.html`
- **Error handling**: try/catch with silent swallows for non-critical paths (`catch (_) {}`)
- **API pattern**: REST endpoints + SSE for streaming chat (`/v1/chat/completions`)
- **Auth**: Ed25519 initData (primary) → Bearer token fallback (`API_SERVER_KEY`)
- **State management**: none (global JS vars, no framework)
- **CSS**: CSS custom properties via `--tg-theme-*` Telegram vars; dark-mode terminal aesthetic
- **Test structure**: none

## Commands
- Install: `cp -r _miniapp /path/to/agent-zero/usr/plugins/`
- Dev: Agent Zero with `_telegram_integration` plugin enabled
- Build: none (single file, no build step)
- Test: none
- Lint: none

## Key Files
- Plugin entry: `_miniapp/plugin.yaml`
- Frontend: `_miniapp/webui/index.html`
- Auth API: `_miniapp/api/auth.py`
- Shell API: `_miniapp/api/shell.py`
- Standalone SPA: `index.html`

## API Endpoints (Gateway — port 8642)
- `GET /health` — CPU/mem/disk/uptime (no auth)
- `GET /api/model-info` — active model name + context length
- `GET /api/session-usage` — cumulative token usage
- `GET /api/jobs` — list cron jobs
- `POST /api/command` — execute slash command
- `GET /api/commands` — list available commands
- `POST /v1/chat/completions` — streaming chat (SSE)

## Required Env Vars
```bash
TELEGRAM_BOT_TOKEN=    # from @BotFather
TELEGRAM_OWNER_ID=     # numeric user ID (not username)
TELEGRAM_ALLOWED_USERS= # comma-separated numeric IDs
API_SERVER_KEY=        # random secret for Bearer fallback
```

## Architecture
```
Telegram Client → index.html (SPA) → Cloudflare Tunnel → Agent Gateway (port 8642)
                  (Ed25519 initData or Bearer token auth)
```
