# Agent Zero Telegram Mini App

> Your Agent Zero control panel, inside Telegram. Chat, monitor, configure, shell in — no browser needed.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Agent Zero](https://img.shields.io/badge/agent--zero-compatible-green.svg)
![Platform](https://img.shields.io/badge/platform-Telegram%20Mini%20App-2CA5E0.svg)
![Build](https://img.shields.io/badge/build-none%20%28single%20file%29-lightgrey.svg)

---

## Features

- 💬 **Chat** — Stream responses from Agent Zero via SSE, right in Telegram
- ⚡ **Live Feed** — Real-time Socket.IO activity stream: tool calls, GEN/USE steps, agent thoughts
- ⚙️ **Config** — Switch LLM models with one tap, toggle plugins, reset or nudge the agent
- 🗂️ **Manage** — Browse chat history, control scheduled tasks, manage your Cloudflare tunnel
- 🖥️ **Shell** — Execute commands inside the A0 Docker container directly from your phone
- 🔐 **Auth** — Telegram `initData` HMAC-SHA256 verification + per-user allowlist — zero manual key entry

---

## Architecture

```
Telegram Client
      │
      ▼
Mini App (index.html — single-file SPA)
      │
      │  HTTPS (Cloudflare Tunnel / ngrok / A0 built-in tunnel)
      ▼
Agent Zero HTTP Server  (port 50080)
      ├── POST /usr/plugins/_miniapp/api/auth       ← initData → api_key
      ├── GET  /usr/plugins/_miniapp/api/shell       ← shell execution
      ├── GET  /usr/plugins/_miniapp/api/presets     ← LLM model list
      ├── GET  /usr/plugins/_miniapp/api/contexts_list
      ├── POST /v1/chat/completions                  ← SSE streaming chat
      └── ws://...                                   ← Socket.IO feed
```

Auth flow:
```
Telegram signs initData with your bot token
  → POST /api/auth validates HMAC-SHA256
  → returns api_key (stored in Telegram CloudStorage)
  → all subsequent calls use X-API-KEY header
```

---

## Plugin Structure

```
a0-plugin/
└── _miniapp/
    ├── plugin.yaml           # Plugin metadata + registration
    ├── default_config.yaml   # Shell timeout, require_auth, allowed_users
    ├── api/
    │   ├── auth.py           # initData → api_key (one-shot, never stored)
    │   ├── shell.py          # Shell endpoint (X-API-KEY required)
    │   ├── contexts_list.py  # Chat history list
    │   ├── presets.py        # LLM preset enumeration
    │   └── reset.py          # Agent context reset
    └── webui/
        ├── index.html        # The entire Mini App (HTML + CSS + JS, no build)
        └── config.html       # Plugin config UI in A0 Settings
```

---

## Requirements

- [Agent Zero](https://github.com/frdel/agent-zero) running (Docker or local)
- `_telegram_integration` plugin enabled in A0 with a valid bot token
- A Telegram bot from [@BotFather](https://t.me/BotFather)
- A public HTTPS URL for your A0 instance (A0 built-in tunnel, `cloudflared`, or ngrok)

---

## Quick Setup

**1. Drop in the plugin**

```bash
cp -r a0-plugin/_miniapp /path/to/agent-zero/usr/plugins/
```

**2. Allow Telegram's origin**

Add to your A0 `usr/.env`:

```env
ALLOWED_ORIGINS=https://web.telegram.org,https://telegram.org
```

**3. Authorize your Telegram user ID**

In the `_telegram_integration` plugin config:

```yaml
bots:
  - token: "YOUR_BOT_TOKEN"
    enabled: true
    allowed_users:
      - 123456789    # your numeric Telegram user ID
```

Leave `allowed_users` empty to allow any user who knows your A0 URL.

**4. Register the Mini App with BotFather**

Your Mini App URL:
```
https://<your-a0-tunnel-url>/usr/plugins/_miniapp/webui/index.html
```

In Telegram → [@BotFather](https://t.me/BotFather):
```
/setmenubutton → select your bot → paste URL → set button label
```

Open your bot and tap the menu button. Done.

---

## Security Notes

- `initData` is verified and discarded in a single request — never persisted
- HMAC-SHA256 validated against your bot token before any key is issued
- All API calls require `X-API-KEY` header
- Shell tab blocks the most dangerous commands (`rm -rf /`, fork bombs, `mkfs`, `dd if=`, `shutdown`, `reboot`)
- Treat shell access as privileged — restrict `allowed_users` accordingly

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| 401 "invalid signature" | Bot token mismatch — verify `_telegram_integration` is enabled with the correct token |
| 503 "Telegram plugin not found" | Enable `_telegram_integration` in A0 → Settings → Plugins |
| 403 "user not authorized" | Add your Telegram user ID to `allowed_users` |
| CORS error / app won't load | Add `https://web.telegram.org` to `ALLOWED_ORIGINS` in `usr/.env` |
| "Open from Telegram" message | Must be opened inside Telegram — `initData` doesn't exist in regular browsers |
| Shell returns "Shell not available" | Confirm plugin is in `usr/plugins/_miniapp/` and restart A0 |

---

## Contributing

PRs welcome. The entire frontend is `a0-plugin/_miniapp/webui/index.html` — a single-file SPA with no build step. Edit it directly.

For backend changes, each API endpoint is a self-contained Python file in `a0-plugin/_miniapp/api/`.

1. Fork the repo
2. Make your changes
3. Test against a local A0 instance
4. Open a PR with a clear description of what and why

---

## License

[MIT](LICENSE)
