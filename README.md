# Agent Zero Telegram Mini App

A control panel for [Agent Zero](https://github.com/frdel/agent-zero) — right inside Telegram.

**NOT a chat interface.** You already chat via the Telegram bot. This is the power panel: real-time activity feed, LLM switcher, plugin toggles, chat management, and a direct shell.

| Tab | What it does |
|-----|--------------|
| ⚡ Feed | Real-time Socket.IO activity stream — tool calls, thoughts, steps |
| ⚙️ Config | LLM model switcher, plugin toggle cards, reset/nudge |
| 💬 Manage | Chat list, scheduler tasks, Cloudflare tunnel widget |
| >_ Shell | Direct shell into the Docker container |

## Install (you already have A0 running)

This is a plugin. Drop it in and it works — no build step, no extra config.

**Step 1 — Copy the plugin**

```bash
cp -r a0-plugin/_miniapp /path/to/agent-zero/usr/plugins/
```

**Step 2 — Allow Telegram's origin**

Add one line to your A0 `usr/.env`:

```
ALLOWED_ORIGINS=https://web.telegram.org,https://telegram.org
```

If you have a tunnel URL you want to test in a browser too, add it there as well.

**Step 3 — Register with BotFather**

Your Mini App URL is:
```
https://<your-a0-tunnel-url>/usr/plugins/_miniapp/webui/index.html
```

In Telegram, open [@BotFather](https://t.me/BotFather):
- `/setmenubutton` → select your bot → button text: `Control Panel` → paste the URL above

That's it. Open your bot and tap the menu button.

> **Where is my tunnel URL?**
> In A0 → Settings → Tunnel → Start Tunnel. Or use `cloudflared tunnel --url http://localhost:50080`.

---

## Prerequisites

- Agent Zero running (Docker recommended)
- `_telegram_integration` plugin enabled in A0 settings with a bot token
- A public HTTPS URL for your A0 instance (A0's built-in tunnel, cloudflared, or ngrok)

## Auth Flow

```
Mini App opens inside Telegram
  ↓
WebApp.initData (signed by Telegram with your bot token)
  ↓
POST <baseUrl>/api/plugins/_miniapp/auth  { init_data: "..." }
  ↓  validates HMAC-SHA256 against your stored bot token
200 { api_key: "<mcp_server_token>" }
  ↓
Stored in Telegram CloudStorage — no manual key entry ever
```

`initData` is never stored — verified and discarded in one request.

## User Authorization

Restrict which Telegram users can connect. In A0's `_telegram_integration` plugin config, set `allowed_users`:

```yaml
bots:
  - token: "YOUR_BOT_TOKEN"
    enabled: true
    allowed_users:
      - 123456789   # your Telegram user ID
```

Leave `allowed_users` empty to allow any Telegram user who knows your A0 URL.

## Shell Tab

Direct bash access to the `/a0` directory in the container.

**Blocked commands:** `rm -rf /`, fork bombs, `mkfs`, `dd if=`, `shutdown`, `reboot`, `halt`, `poweroff`.

Timeout: **30 seconds**. Output cap: **50 KB**.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| 401 "invalid signature" | Bot token mismatch — verify `_telegram_integration` is enabled and token matches your bot |
| 503 "Telegram plugin not found" | Enable `_telegram_integration` in A0 → Settings → Plugins |
| 500 "API key not configured" | Set an API key in A0 Settings |
| 403 "user not authorized" | Add your Telegram user ID to `allowed_users` in `_telegram_integration` config |
| App won't load / CORS error | Add `https://web.telegram.org` to `ALLOWED_ORIGINS` in `usr/.env` |
| "Open from Telegram" message | Must be opened inside Telegram's built-in browser — `initData` doesn't exist in regular browsers |
| Shell returns "Shell not available" | Plugin volume mount not working — verify the plugin is in `usr/plugins/_miniapp/` and restart |

## File Structure

```
a0-TelegramMiniApp/
├── index.html                   # The entire Mini App (single-file SPA, no build step)
├── a0-plugin/
│   └── _miniapp/
│       ├── plugin.yaml          # Plugin metadata
│       ├── default_config.yaml  # Plugin config template
│       ├── api/
│       │   ├── auth.py          # initData → api_key (no auth required)
│       │   └── shell.py         # Shell endpoint (requires X-API-KEY)
│       └── webui/
│           └── index.html       # Same file — served at /usr/plugins/_miniapp/webui/
├── tests/
│   └── test_shell.py            # pytest tests for shell.py (19 tests)
└── docker-compose.example.yml   # Only needed if starting A0 from scratch
```

## Fresh Install (starting from scratch)

If you don't have A0 running yet:

```bash
cp docker-compose.example.yml docker-compose.yml
# Edit docker-compose.yml — set ALLOWED_ORIGINS and your API keys
docker-compose up -d
```

Then follow the 3-step install above.

## Security

- `initData` is never stored — verified and discarded in a single request
- HMAC-SHA256 validation before issuing any key
- All API calls use `X-API-KEY` with the MCP server token
- Shell blocklist prevents the most dangerous commands — treat shell access as privileged

## License

MIT
