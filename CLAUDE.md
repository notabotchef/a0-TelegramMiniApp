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
├── Reference/
│   └── hermes-telegram-miniapp/   # Reference SPA to adapt from
│       ├── index.html             # Entire app — ~75KB single file
│       ├── .env.example           # Required env vars template
│       ├── systemd/               # Production service template
│       ├── tunnel/                # Cloudflare tunnel config template
│       └── README.md              # Full setup guide
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
- Install: `cp Reference/hermes-telegram-miniapp/index.html ~/.hermes/miniapp/index.html`
- Dev: `hermes gateway run` (backend gateway, port 8642)
- Build: none (single file, no build step)
- Test: none
- Lint: none

## Key Files
- Entry point: `Reference/hermes-telegram-miniapp/index.html`
- Env config: `Reference/hermes-telegram-miniapp/.env.example`
- Systemd service: `Reference/hermes-telegram-miniapp/systemd/hermes-gateway.service`
- Tunnel config: `Reference/hermes-telegram-miniapp/tunnel/cloudflared-config.yml`

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
