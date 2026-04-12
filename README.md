# Agent Zero Telegram Mini App

A Telegram Mini App that gives you a control panel for [Agent Zero](https://github.com/frdel/agent-zero) — right inside Telegram.

**NOT a chat interface** — you already chat via the Telegram bot. This is the power panel: real-time activity feed, LLM switcher, plugin toggles, chat management, and a direct shell.

## Features (planned)

| Tab | Status | What it does |
|-----|--------|--------------|
| ⚡ Feed | Phase 2 | Real-time Socket.IO activity stream — tool calls, thoughts, steps |
| ⚙️ Config | Phase 3 | LLM model switcher, plugin toggle cards, reset/nudge |
| 💬 Manage | Phase 4 | Chat list, scheduler tasks, tunnel widget |
| >_ Shell | Phase 5 | Direct shell with subprocess output streaming |

## Prerequisites

- A running [Agent Zero](https://github.com/frdel/agent-zero) instance (Docker recommended)
- A Telegram bot configured in Agent Zero via the `_telegram_integration` plugin
- Docker + docker-compose

## Setup

### 1. Clone this repo

```bash
git clone https://github.com/yourusername/agent0-telegram-miniapp
cd agent0-telegram-miniapp
```

### 2. Configure Docker

```bash
cp docker-compose.example.yml docker-compose.yml
# Edit docker-compose.yml if needed (image, ports, etc.)
```

The example file already sets:
- `ALLOWED_ORIGINS=https://web.telegram.org` (required for Telegram WebView)
- Volume mount: `./a0-plugin/_miniapp:/a0/usr/plugins/_miniapp`

### 3. Start Agent Zero

```bash
docker-compose up -d
```

### 4. Enable the Telegram integration in Agent Zero

1. Open Agent Zero at `http://localhost:50080`
2. Go to Settings → Plugins
3. Enable `_telegram_integration` and enter your bot token
4. The `_miniapp` plugin should appear automatically (it's mounted via volume)

### 5. Get your public URL

Agent Zero needs a public HTTPS URL for the Mini App to reach it. Options:
- **Built-in tunnel**: A0 has a tunnel feature — start it from the UI and note the URL
- **Cloudflare Tunnel**: `cloudflared tunnel --url http://localhost:50080`
- **ngrok**: `ngrok http 50080`

### 6. Set up BotFather

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. `/setmenubutton` → select your bot → enter:
   - Button text: `Open Panel`
   - URL: `https://<your-tunnel-url>/index.html`
   
   **Or** use a Web App via `/newapp` for a more integrated experience.

### 7. Open the Mini App

1. Open your Telegram bot
2. Tap the menu button (or the app button)
3. Enter your public Agent Zero URL when prompted
4. Done — your Telegram identity is used for auth automatically

## Auth Flow

```
App opens in Telegram
  ↓
WebApp.initData (signed by Telegram servers)
  ↓
POST /api/plugins/_miniapp/auth  {init_data: "..."}
  ↓  (HMAC-SHA256 validated on A0 side using your bot token)
200 {api_key: "<mcp_server_token>"}
  ↓
Stored in Telegram CloudStorage — no API key needed from you
```

## No API Key Entry

Unlike other setups, this Mini App **never asks for an API key**. Your Telegram identity (validated via HMAC-SHA256 using your bot's token) is the credential. The app exchanges it for the MCP server token automatically.

## Development

No build step. Edit `index.html` directly.

To test locally (without Telegram):
- The app will show "Open from Telegram" if `WebApp.initData` is absent
- Use [Telegram's test environment](https://core.telegram.org/bots/webapps#testing-mini-apps) for real initData testing

## File Structure

```
agent0-telegram-miniapp/
├── index.html                          # The entire Mini App (single file SPA)
├── docker-compose.example.yml          # Copy-paste Docker setup
├── a0-plugin/
│   └── _miniapp/
│       ├── plugin.yaml                 # Plugin metadata
│       ├── default_config.yaml         # Plugin config template
│       └── api/
│           ├── auth.py                 # initData → api_key endpoint (no auth required)
│           └── shell.py                # Shell endpoint (Phase 5)
└── README.md
```

## Security Notes

- `initData` is **never stored** — it's sent to `auth.py` and immediately discarded
- `auth.py` validates the HMAC-SHA256 signature using your bot token before issuing any key
- The `_miniapp/api/auth.py` endpoint is deliberately unauthenticated — it IS the authentication
- All other API calls use `X-API-KEY` header with the MCP server token
