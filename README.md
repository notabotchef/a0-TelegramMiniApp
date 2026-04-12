# Agent Zero Telegram Mini App

A Telegram Mini App that gives you a control panel for [Agent Zero](https://github.com/frdel/agent-zero) — right inside Telegram.

**NOT a chat interface** — you already chat via the Telegram bot. This is the power panel: real-time activity feed, LLM switcher, plugin toggles, chat management, and a direct shell.

## Features

| Tab | What it does |
|-----|--------------|
| ⚡ Feed | Real-time Socket.IO activity stream — tool calls, thoughts, steps |
| ⚙️ Config | LLM model switcher, plugin toggle cards, reset/nudge |
| 💬 Manage | Chat list, scheduler tasks, Cloudflare tunnel widget |
| >_ Shell | Direct shell into the Docker container (subprocess, streamed output) |

## Prerequisites

- A running [Agent Zero](https://github.com/frdel/agent-zero) instance (Docker recommended)
- A Telegram bot configured in Agent Zero via the `_telegram_integration` plugin
- Docker + docker-compose

## Setup

### 1. Clone this repo

```bash
git clone https://github.com/notabotchef/agent-zero-telegram-miniapp
cd agent-zero-telegram-miniapp
```

### 2. Configure Docker

```bash
cp docker-compose.example.yml docker-compose.yml
# Edit docker-compose.yml if needed (image, ports, env)
```

The example already sets:
- `ALLOWED_ORIGINS=https://web.telegram.org,https://telegram.org` — required for Telegram WebView
- Volume mount: `./a0-plugin/_miniapp:/a0/usr/plugins/_miniapp` — drops the plugin into A0 automatically

### 3. Start Agent Zero

```bash
docker-compose up -d
```

### 4. Enable the Telegram integration in Agent Zero

1. Open Agent Zero at `http://localhost:50080`
2. Go to **Settings → Plugins**
3. Enable `_telegram_integration` and enter your bot token + (optionally) `allowed_users`
4. The `_miniapp` plugin appears automatically — no additional configuration needed

### 5. Get a public HTTPS URL

The Mini App must be served over HTTPS (Telegram's requirement). Options:

**Option A — Built-in A0 tunnel (recommended)**
1. In Agent Zero, go to Settings → Tunnel
2. Click **Start Tunnel** — A0 will start a Cloudflare tunnel
3. Copy the `https://...trycloudflare.com` URL

**Option B — cloudflared CLI**
```bash
cloudflared tunnel --url http://localhost:50080
```

**Option C — ngrok**
```bash
ngrok http 50080
```

### 6. Register the Mini App with BotFather

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newapp` → select your bot → follow prompts
3. Set **Web App URL** to `https://<your-public-url>/index.html`

Or for a simple menu button:
1. Send `/setmenubutton` → select your bot
2. Enter button text: `Control Panel`
3. Enter URL: `https://<your-public-url>/index.html`

### 7. Open the Mini App

1. Open your Telegram bot
2. Tap the menu button (or app button)
3. Enter your public Agent Zero URL when prompted
4. Done — Telegram identity handles auth automatically, no API key needed

## Auth Flow

```
Mini App opens inside Telegram
  ↓
WebApp.initData (signed by Telegram's servers with your bot token)
  ↓
POST <baseUrl>/api/plugins/_miniapp/auth  { init_data: "..." }
  ↓  (server validates HMAC-SHA256 using stored bot token)
200 { api_key: "<mcp_server_token>" }
  ↓
Stored in Telegram CloudStorage (no manual key entry ever)
```

initData is **never stored** — verified and discarded in one request.

## Docker Configuration

Key environment variables for your `docker-compose.yml`:

```yaml
environment:
  ALLOWED_ORIGINS: "https://web.telegram.org,https://telegram.org"
  # Add your Agent Zero env vars below
  # ANTHROPIC_API_KEY: ...
  # etc.

volumes:
  - ./a0-plugin/_miniapp:/a0/usr/plugins/_miniapp
```

`ALLOWED_ORIGINS` is **required** — without it Telegram's WebView cannot reach your A0 instance (CORS block).

## User Authorization

Optionally restrict which Telegram users can authenticate. In A0's `_telegram_integration` plugin config, set `allowed_users` to a list of Telegram user IDs:

```yaml
bots:
  - token: "YOUR_BOT_TOKEN"
    enabled: true
    allowed_users:
      - 123456789   # your Telegram user ID
      - 987654321
```

Leave `allowed_users` empty to allow any Telegram user who knows your A0 URL.

## Shell Tab

The Shell tab provides direct bash access to the `/a0` directory inside the Docker container.

**Safety**: The following commands are blocked server-side:
- `rm -rf /` and variants
- Fork bombs (`:(){ :|:& };:`)
- `mkfs`, `dd if=`, `shutdown`, `reboot`, `halt`, `poweroff`

Commands time out after **30 seconds**. Output is capped at **50 KB**.

## Troubleshooting

**"Open from Telegram" — app won't load**
→ The app must be opened inside Telegram's built-in browser. `WebApp.initData` does not exist in regular browsers.

**401 "invalid signature"**
→ Bot token mismatch. Verify the `_telegram_integration` plugin is enabled in A0 and the token matches your bot.

**503 "Telegram plugin not found"**
→ The `_telegram_integration` plugin is not enabled. Open A0 → Settings → Plugins → enable it.

**500 "Agent Zero API key not configured"**
→ A0 has no MCP server token set. Open A0 → Settings → set an API key.

**403 "user not authorized"**
→ Your Telegram user ID is not in the `allowed_users` list. Add it in A0's `_telegram_integration` config, or clear `allowed_users` to allow everyone.

**Connection timed out on setup**
→ `ALLOWED_ORIGINS` is missing from `docker-compose.yml`. Add it and restart A0.

**Shell tab returns "Shell not available"**
→ The `_miniapp` plugin volume mount is not working. Verify `docker-compose.yml` volume and restart.

## File Structure

```
agent-zero-telegram-miniapp/
├── index.html                          # The entire Mini App (~120KB, single-file SPA)
├── docker-compose.example.yml          # Copy-paste Docker setup
├── a0-plugin/
│   └── _miniapp/
│       ├── plugin.yaml                 # Plugin metadata
│       ├── default_config.yaml         # Plugin config template
│       └── api/
│           ├── auth.py                 # initData → api_key (no auth required)
│           └── shell.py                # Shell endpoint (requires X-API-KEY)
├── tests/
│   └── test_auth.py                    # pytest tests for auth.py (17 tests)
└── README.md
```

## Security Notes

- `initData` is **never stored** — verified and discarded in a single request
- `auth.py` validates HMAC-SHA256 before issuing any key — standard Telegram Mini App security
- `auth.py` is intentionally `skip_auth = True` — it IS the authentication endpoint
- All other API calls use `X-API-KEY` with the MCP server token
- Shell blocklist prevents the most dangerous commands, but treat shell access as privileged

## Contributing

1. Fork + branch from `main`
2. Edit `index.html` directly — no build step
3. For plugin changes: edit files under `a0-plugin/_miniapp/`
4. Run auth tests: `python -m pytest tests/test_auth.py -v`
5. Test inside Telegram (required — `initData` only works there)
6. Open a PR

## License

MIT
