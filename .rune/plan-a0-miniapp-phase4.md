# Phase 4: Manage Tab — Chats + Scheduler + Tunnel

## Goal
Manage A0 data remotely: browse/delete/create chat contexts, view and control scheduled tasks,
see tunnel status and start/stop it from Telegram.

## Data Flow

### Chats section
```
Tab activated
  ↓
POST /api/history_get {context: ""} → all contexts list
  (if returns list: [{id, title, created, message_count}])
  OR: try context IDs stored locally
  ↓
Render chat cards: title, date, message count, delete btn
```

### Scheduler section
```
POST /api/scheduler_tasks_list {}
  → [{id, name, enabled, schedule, last_run, next_run, status}]
  ↓
Render task cards with: name, schedule, status dot, Run/Delete actions
```

### Tunnel widget (header, all tabs)
```
On app load:
  POST /api/tunnel {action: "get"}
  → {tunnel_url, is_running}
  ↓
Header badge: 🌐 URL (copy on tap) if running
             🌐 Start if not running
```

## Code Contracts

```javascript
// Manage state
let chatContexts = []     // [{id, title, created, message_count}]
let scheduledTasks = []   // [{id, name, enabled, schedule, last_run, next_run}]
let tunnelUrl = null      // current tunnel URL or null
let tunnelRunning = false

// Chats
async function loadChats() → void
async function deleteChat(id) → void
  // WebApp.showConfirm("Delete this conversation?", cb)
  // POST /api/chat_remove {context: id}
async function newChat() → void
  // POST /api/chat_create {} → {ctxid}
  // Prepend to chat list

// Scheduler
async function loadTasks() → void
async function runTask(id) → void
  // POST /api/scheduler_task_run {id}
async function deleteTask(id) → void
  // WebApp.showConfirm → POST /api/scheduler_task_delete {id}

// Tunnel
async function loadTunnel() → void
  // POST /api/tunnel {action: "get"}
async function startTunnel() → void
  // POST /api/tunnel {action: "create", provider: "cloudflared"}
  // Poll /api/tunnel {action:"get"} every 2s until tunnel_url populated (max 30s)
async function stopTunnel() → void
  // POST /api/tunnel {action: "stop"}
function copyTunnelUrl() → void
  // navigator.clipboard.writeText(tunnelUrl)
  // Toast "URL copied"
```

## File
- **File**: `index.html` — `#manage-panel` section + header tunnel widget + `<script>`

## Tasks

### Wave 1 (parallel)

#### Task 1a — Manage panel HTML
- **File**: `index.html` — `#manage-panel`
- **touches**: [index.html]
- **provides**: [manage DOM]
- Structure:
  ```
  #manage-panel.panel
    .panel-scroll
      .section#chats-section
        .section-header "Conversations" + btn "New Chat" (right)
        .chat-list#chat-list
        
      .section#tasks-section  
        .section-header "Scheduled Tasks" + badge(count)
        .task-list#task-list
  ```

#### Task 1b — Header tunnel widget HTML + CSS
- **File**: `index.html` — header area
- **touches**: [index.html]
- **provides**: [tunnel badge in header]
- Small badge right of title: "🌐 active" (green dot) or "🌐 off" (gray dot)
- Tap → bottom sheet / modal with: current URL, Copy btn, Stop/Start btn
- Bottom sheet: slides up, dark overlay, rounded top corners

#### Task 1c — Manage + tunnel CSS
- **File**: `index.html` — `<style>`
- **touches**: [index.html]
- **provides**: [chat card, task card, tunnel modal styles]
- `.chat-card` — row: title left, date + delete icon right
- `.task-card` — row: status dot + name, schedule text below; Run + Delete btns right
- `.task-card .status-dot.running` — green pulse
- `.task-card .status-dot.failed` — red
- `.tunnel-sheet` — fixed bottom sheet, `--sec-bg`, border-radius top 16px
- `.tunnel-url` — monospace, truncated with `...`, green color

### Wave 2 (depends on 1a + 1b)

#### Task 2a — Chat list fetch + render
- **File**: `index.html` — `<script>`
- **depends_on**: [task-1a]
- **touches**: [index.html]
- **provides**: [loadChats(), renderChatList(), deleteChat(), newChat()]
- `loadChats()`: POST `/api/history_get {context: ""}` — if endpoint returns list, use it
  - Fallback: A0 may not return a context list; if so, show "Chat management not available in this A0 version"
- `deleteChat()`: Telegram confirm → POST `chat_remove` → remove card from DOM
- `newChat()`: POST `chat_create` → toast "New conversation created"
- Date format: relative ("2 hours ago", "Yesterday", "Apr 10")

#### Task 2b — Scheduler fetch + render
- **File**: `index.html` — `<script>`
- **depends_on**: [task-1a]
- **touches**: [index.html]
- **provides**: [loadTasks(), renderTaskList(), runTask(), deleteTask()]
- `loadTasks()`: POST `/api/scheduler_tasks_list {}`
- Status colors: enabled+running=green, enabled+idle=blue, disabled=gray, failed=red
- `runTask()`: POST `scheduler_task_run {id}` → toast "Task triggered ✓"
- `deleteTask()`: Telegram confirm → POST `scheduler_task_delete {id}` → remove card

#### Task 2c — Tunnel widget logic
- **File**: `index.html` — `<script>`
- **depends_on**: [task-1b]
- **touches**: [index.html]
- **provides**: [loadTunnel(), startTunnel(), stopTunnel(), copyTunnelUrl()]
- `loadTunnel()`: called on app init (Phase 1 init flow)
- Starting tunnel: show spinner in badge, poll every 2s for URL, timeout 30s
- Stopping: confirm dialog → POST stop → badge updates to "off"
- Copy: `navigator.clipboard.writeText(url)` + haptic + toast

### Wave 3 (depends on 2a + 2b + 2c)

#### Task 3a — loadManageTab() + init wiring
- **File**: `index.html` — `<script>`
- **depends_on**: [task-2a, task-2b, task-2c]
- **touches**: [index.html]
- **provides**: [loadManageTab()]
- `loadManageTab()`: `Promise.allSettled([loadChats(), loadTasks()])` on tab activate
- Cache 30s (scheduler tasks change more frequently than plugins)
- Wire tunnel load into Phase 1 `init()` flow: `loadTunnel()` after auth

## Failure Scenarios

| When | Then | Error |
|------|------|-------|
| `history_get` doesn't return context list | Show "Chat list not available. A0 API may not support it." | Degraded graceful state |
| `scheduler_tasks_list` returns empty | Show "No scheduled tasks" | Empty state with icon |
| Tunnel start times out (30s) | Show error | "Tunnel failed to start. Check Cloudflare credentials." |
| `chat_remove` fails | Revert UI, toast error | "Failed to delete conversation" |
| `scheduler_task_run` fails | Toast error | "Task trigger failed: <reason>" |
| clipboard API unavailable | Fall back to prompt() | `prompt("Copy this URL:", tunnelUrl)` |

## Rejection Criteria
- DO NOT delete chats without Telegram confirm dialog
- DO NOT auto-start the tunnel — only on user tap
- DO NOT poll scheduler tasks on a timer — only load on tab open
- DO NOT show raw context IDs as chat titles — use truncated first message or "Conversation <date>"

## Cross-Phase Context
### Assumes from prior phases
- Phase 1: `api()`, init flow, CloudStorage
- Phase 2: Socket.IO connected
- Phase 3: CSS patterns established

### Exports for Phase 5
- Tunnel widget (reused/polished in Phase 5)
- `loadManageTab()` called pattern

## Acceptance Criteria
- [ ] Manage tab shows list of past conversations with delete buttons
- [ ] "New Chat" creates context, toast confirms
- [ ] Delete chat → Telegram confirm dialog → card removed
- [ ] Scheduled tasks render with status dots
- [ ] "Run" button triggers task, toast confirms
- [ ] Tunnel badge in header shows current status
- [ ] Tapping tunnel badge opens sheet with URL + copy button
- [ ] Start tunnel → spinner → URL appears → badge turns green

## Test Tasks
- Manual: open Manage tab → verify chats and tasks load
- Manual: delete a chat → confirm → verify removed
- Manual: trigger a scheduled task → verify toast
- Manual: tap tunnel badge → start tunnel → verify URL appears
- Manual: copy tunnel URL → verify clipboard + toast

---

## Outcome Block
**What Was Planned**: Phase 4 — chat list, scheduler management, tunnel widget.

**Immediate Next Action**: `rune:cook` on `feat/phase-4-manage`.

**How to Measure**:
```bash
curl -X POST http://localhost:50080/api/scheduler_tasks_list \
  -H "X-API-KEY: <key>" -H "Content-Type: application/json" -d '{}'

curl -X POST http://localhost:50080/api/tunnel \
  -H "X-API-KEY: <key>" -H "Content-Type: application/json" \
  -d '{"action": "get"}'
```
