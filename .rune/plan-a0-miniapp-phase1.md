# Phase 1: A0 Plugin + Scaffold + Auth

## Goal
Two deliverables: (1) `_miniapp` Agent Zero plugin that validates Telegram initData and exposes shell.
(2) `index.html` shell with setup screen (URL only, no API key) + initData handshake flow.

## Data Flow

### Auth handshake
```
App Open
  ↓
WebApp.ready() + WebApp.expand()
isTelegram = !!WebApp.initData  ← must be true
  ↓
CloudStorage.getItem('a0_base_url') → loaded?
  NO → show setup screen (user enters URL only)
  YES → skip to connection test
  ↓
GET <baseUrl>/api/health (4s timeout)
  ↓ 200 OK
POST <baseUrl>/api/plugins/_miniapp/auth
  body: {init_data: WebApp.initData}
  ↓ 200 {api_key: "..."}
CloudStorage.setItem('a0_api_key', api_key)
  ↓
Show main app (4-tab layout)
```

### Plugin auth validation (Python)
```
Receive init_data string
  ↓
Parse: split on '&', extract hash field
  ↓
data_check_string = sorted remaining fields joined by '\n'
  ↓
secret_key = HMAC-SHA256("WebAppData", bot_token)
  ↓
expected_hash = HMAC-SHA256(secret_key, data_check_string).hex()
  ↓
expected_hash == hash? → 200 {api_key: mcp_server_token}
                       → 401 {error: "invalid signature"}
```

## Code Contracts

### Python plugin files

```python
# a0-plugin/_miniapp/plugin.yaml
name: "miniapp"
label: "Telegram Mini App"
description: "Auth + shell bridge for the Agent Zero Telegram Mini App"
version: "0.1.0"
enabled: true

# a0-plugin/_miniapp/default_config.yaml
allowed_telegram_bots: []  # list of bot names from _telegram_integration config

# a0-plugin/_miniapp/api/auth.py
# Called: POST /api/plugins/_miniapp/auth  (no auth required, no CSRF)
# Input: {init_data: str}
# Output 200: {api_key: str}
# Output 401: {error: str}
# Skips: requires_auth, requires_csrf (registered via skip_auth=True)

# a0-plugin/_miniapp/api/shell.py  ← skeleton only in Phase 1, implemented in Phase 5
# Called: POST /api/plugins/_miniapp/shell
# Input: {cmd: str, context_id: str}
# Requires: X-API-KEY auth
```

### JavaScript (index.html)

```javascript
const WebApp = window.Telegram?.WebApp
const CS = WebApp?.CloudStorage
let baseUrl = ''    // e.g. "https://my-agent-zero.com"
let apiKey = ''     // received from /api/plugins/_miniapp/auth

// Config
async function loadConfig() → {baseUrl, apiKey} | null
async function saveConfig(url, key) → void  // CloudStorage + localStorage

// Auth
async function doHandshake() → {ok: bool, api_key?: string, error?: string}
  // POST baseUrl/api/plugins/_miniapp/auth  {init_data: WebApp.initData}

// API helper
async function api(path, opts={}) → any
  // fetch with X-API-KEY header, Content-Type: application/json, 15s default timeout

// Connection
async function testConnection(url) → {ok: bool, error?: string}
  // GET url/api/health, 4s timeout

// Panels
function showSetup() → void
function hideSetup() → void
function showApp() → void   // reveal 4-tab layout

// Init
async function init() → void
  // Called on DOMContentLoaded
```

## Files

- **`a0-plugin/_miniapp/plugin.yaml`** — new
- **`a0-plugin/_miniapp/default_config.yaml`** — new
- **`a0-plugin/_miniapp/api/auth.py`** — new
- **`a0-plugin/_miniapp/api/shell.py`** — skeleton only (Phase 5 implements)
- **`docker-compose.example.yml`** — new
- **`index.html`** — new (skeleton + setup screen)
- **`README.md`** — new (setup instructions)
- **`.gitignore`** — new

## Tasks

### Wave 1 (parallel, independent)

#### Task 1a — `auth.py` plugin endpoint
- **File**: `a0-plugin/_miniapp/api/auth.py`
- **touches**: [a0-plugin/_miniapp/api/auth.py]
- **provides**: [POST /api/plugins/_miniapp/auth]
- Implement Telegram initData HMAC-SHA256 validation
- Get bot token: `plugins.get_plugin_config("_telegram_integration")["bots"][0]["token"]`
- Get MCP server token: `settings.get_settings()["mcp_server_token"]` or from `settings.json`
- Return `{api_key: mcp_token}` on success, `{error: "..."}` on failure
- Register as no-auth endpoint (A0 framework: check how `webhook.py` skips auth)
- Use only stdlib: `hmac`, `hashlib`, `urllib.parse` — no new deps

#### Task 1b — plugin metadata files
- **File**: `a0-plugin/_miniapp/plugin.yaml`, `a0-plugin/_miniapp/default_config.yaml`
- **touches**: [plugin.yaml, default_config.yaml]
- **provides**: [plugin registration]

#### Task 1c — `shell.py` skeleton
- **File**: `a0-plugin/_miniapp/api/shell.py`
- **touches**: [a0-plugin/_miniapp/api/shell.py]
- **provides**: [skeleton for Phase 5]
- Returns `{error: "not implemented in v0.1"}` — stub only

#### Task 1d — docker-compose.example.yml
- **File**: `docker-compose.example.yml`
- **touches**: [docker-compose.example.yml]
- **provides**: [copy-paste Docker setup]
- Volume mount: `./a0-plugin/_miniapp:/a0/usr/plugins/_miniapp`
- Env vars: `ALLOWED_ORIGINS=https://web.telegram.org`
- Port: `50080:80`

### Wave 2 (parallel)

#### Task 2a — HTML skeleton + CSS variables
- **File**: `index.html`
- **touches**: [index.html]
- **provides**: [DOM structure, CSS vars, tab layout shell]
- Scripts: `telegram-web-app.js?62`, `socket.io/4.7.5/socket.io.min.js`
- CSS vars: `--bg: #0d0d0d`, `--accent: #22c55e`, Telegram theme var fallbacks
- Panels: `#setup-panel` (visible), `#app-panel` (hidden, contains tab bar + 4 panels)
- Tab bar: Feed ⚡, Config ⚙, Manage 💬, Shell >_ 
- 4 empty panels: `#feed-panel`, `#config-panel`, `#manage-panel`, `#shell-panel`
- Header: "Agent Zero" title, connection dot (right), tunnel badge (right)

#### Task 2b — Setup screen UI
- **File**: `index.html` — `#setup-panel`
- **touches**: [index.html]
- **provides**: [showSetup(), first-run URL entry]
- Agent Zero logo (inline SVG green hexagon or "A0" text mark)
- Single input: Base URL (`https://your-agent-zero.com`)
- Hint: "No API key needed — your Telegram identity authenticates you"
- "Connect" button → disabled while loading
- Error state: red inline message below input
- Footer: link to README for help

### Wave 3 (depends on 2a + 2b + 1a)

#### Task 3a — Init + auth + `api()` helper
- **File**: `index.html` — `<script>`
- **depends_on**: [task-2a, task-2b, task-1a]
- **touches**: [index.html]
- **provides**: [init(), doHandshake(), api(), loadConfig(), saveConfig(), testConnection()]
- `init()`: WebApp.ready() → expand() → loadConfig() → if url: testConnection() → doHandshake() → showApp() else showSetup()
- `doHandshake()`: POST auth endpoint with `{init_data: WebApp.initData}`
- `api()`: fetch + X-API-KEY header + JSON parse + error handling
- `testConnection()`: GET /health, 4s timeout

#### Task 3b — README.md
- **File**: `README.md`
- **depends_on**: [task-1d]
- **touches**: [README.md]
- **provides**: [setup instructions]
- Steps: Clone repo → copy docker-compose.example.yml → add ALLOWED_ORIGINS → mount plugin → get URL from A0 tunnel → set in BotFather → open in Telegram

## Failure Scenarios

| When | Then | Error |
|------|------|-------|
| `WebApp.initData` is empty (opened in browser, not Telegram) | Show full-screen error | "Please open this app from Telegram" |
| `/api/health` unreachable | Show error on Connect btn | "Cannot reach Agent Zero. Check URL and that ALLOWED_ORIGINS is set." |
| `/api/plugins/_miniapp/auth` returns 401 | Show error | "Auth failed — is the Telegram plugin active with your bot?" |
| `_telegram_integration` plugin not found in A0 | `auth.py` returns 503 | "Telegram plugin not found. Enable it in Agent Zero settings." |
| `mcp_server_token` not set in A0 | `auth.py` returns 500 | "Agent Zero API key not configured. Set it in A0 settings." |
| CloudStorage unavailable | Fall back to localStorage | Silent fallback |

## Rejection Criteria
- DO NOT store `initData` beyond the handshake call — discard after auth
- DO NOT implement API key entry — initData only
- DO NOT use `eval()` anywhere
- DO NOT add CSS frameworks (Tailwind, Bootstrap) — keep it inline CSS, single file
- DO NOT skip the health check before calling auth — confirm server is reachable first

## Cross-Phase Context
### Assumes from prior phases
- Nothing (Phase 1 is foundation)

### Exports for Phase 2+
- `baseUrl`, `apiKey` globals
- `api(path, opts)` helper
- `switchTab(name)` function
- 4 empty panel DOM elements ready to populate
- CSS variable system + Agent Zero color palette
- Socket.IO CDN loaded (ready to connect in Phase 2)

## Acceptance Criteria
- [ ] Fresh open in Telegram → setup screen with URL input only
- [ ] Enter valid A0 URL → connects, handshakes, shows 4-tab app
- [ ] Enter bad URL → inline error, no crash
- [ ] Reopen app → setup screen skipped, goes straight to app
- [ ] Opened in browser → "Open from Telegram" error shown
- [ ] A0 plugin installed + Docker mounted → `auth.py` endpoint responds 200
- [ ] docker-compose.example.yml has working volume mount syntax

## Test Tasks
- Manual: open in Telegram with no config → setup screen shown
- Manual: enter correct A0 URL → see 4-tab app
- Python unit test: test `auth.py` HMAC validation with known test vector from Telegram docs
- Manual: run `docker-compose -f docker-compose.example.yml up` → verify plugin loads

## Traceability Matrix
| Req | Task | Test |
|-----|------|------|
| initData handshake | Task 1a, 3a | Python unit test |
| No API key entry | Task 2b | Manual review |
| Docker mount | Task 1d | docker-compose test |

---

## Outcome Block
**What Was Planned**: Phase 1 — `_miniapp` A0 plugin with auth endpoint, `index.html` skeleton, setup screen, initData handshake flow.

**Immediate Next Action**: `rune:cook` on branch `feat/phase-1-scaffold` to build `a0-plugin/` directory + `index.html` skeleton.

**How to Measure**:
```bash
# Verify plugin files exist
ls a0-plugin/_miniapp/api/

# Verify index.html created
wc -l index.html  # target ~250 LOC for Phase 1

# Test auth endpoint manually
curl -X POST http://localhost:50080/api/plugins/_miniapp/auth \
  -H "Content-Type: application/json" \
  -d '{"init_data": "test"}' 
# Expected: 401 {"error": "invalid signature"}
```
