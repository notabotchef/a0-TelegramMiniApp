# Developer Guide: Agent0TelegramApp

## What This Does
Terminal-style Telegram Mini App for an AI agent. Users chat with their agent, monitor system health, and manage cron jobs — all from inside Telegram.

## Quick Setup

```bash
# 1. Set env vars
cp Reference/hermes-telegram-miniapp/.env.example ~/.hermes/.env
# Edit ~/.hermes/.env — fill in TELEGRAM_BOT_TOKEN, TELEGRAM_OWNER_ID, API_SERVER_KEY

# 2. Install mini app
mkdir -p ~/.hermes/miniapp
cp Reference/hermes-telegram-miniapp/index.html ~/.hermes/miniapp/index.html

# 3. Start gateway (requires hermes agent v0.8.0+)
hermes gateway run

# 4. Expose to internet (quick tunnel for testing)
cloudflared tunnel --url http://localhost:8642

# 5. Register URL with @BotFather
# /setmenubutton → your bot → https://YOUR_TUNNEL_URL/miniapp/index.html
```

## Key Files
- `Reference/hermes-telegram-miniapp/index.html` — entire app (~75KB, single file)
- `Reference/hermes-telegram-miniapp/.env.example` — required env vars
- `Reference/hermes-telegram-miniapp/systemd/hermes-gateway.service` — production systemd template
- `Reference/hermes-telegram-miniapp/tunnel/cloudflared-config.yml` — named tunnel config

## How to Contribute
1. Branch from main
2. Edit `index.html` directly (no build step)
3. Test in Telegram (required — initData only works inside Telegram's browser)
4. Open a PR

## Common Issues

**401 when sending messages** → `TELEGRAM_BOT_TOKEN` wrong or missing. Verify: `curl https://api.telegram.org/bot<TOKEN>/getMe`

**"Invalid API key" on cron/status tab** → `API_SERVER_KEY` not set, or mismatch. Clear mini app local storage in Telegram → ... → Clear storage.

**initData not working in browser** → Expected. `initData` only exists inside Telegram's built-in browser. Use Bearer fallback (`API_SERVER_KEY`) for browser testing.

**Tunnel URL changed** → Free `cloudflared tunnel --url` gives random URL on restart. Use a named tunnel for stable URLs (see Step 5B in README).
