# Phase 2: Feed Tab — Real-Time Activity Stream

## Goal
The killer feature: see exactly what Agent Zero is doing in real-time.
Socket.IO connection → display tool calls, agent thoughts, step progress as they happen.
Pause/resume stream. Clear feed. Works even when A0 is running a task started from the Telegram bot.

## Data Flow
```
Tab opens (Feed is default/active tab)
  ↓
connectSocket() → io(baseUrl, {auth: {handlers: ['webui']}})
  ↓
socket.on('connect') → setConn('online')
socket.on('disconnect') → setConn('offline'), attempt reconnect
  ↓
Events arrive continuously:
  'agent_thought'   → addFeedItem('thought', data)
  'agent_tool'      → addFeedItem('tool', data)     ← tool call start
  'agent_response'  → updateFeedStream(data.content) ← A0 typing
  'agent_complete'  → finalizeFeedStream()
  'agent_error'     → addFeedItem('error', data)
  ↓
Feed renders: chronological list, newest at bottom
Auto-scroll if near bottom; scroll-to-bottom btn if scrolled up
```

**Note**: Socket.IO event names MUST be verified against running A0 instance before coding.
During Phase 2 start: connect to test A0 → log raw events → confirm schema.

## Code Contracts

```javascript
// Socket.IO state
let socket = null
let feedPaused = false

// Connect (called on Feed tab activate or app init)
function connectSocket() → void
  // io(baseUrl, {transports:['websocket','polling'], auth:{handlers:['webui']}})
  // Register: connect, disconnect, connect_error + all agent events

// Feed rendering
function addFeedItem(type, data) → HTMLElement
  // type: 'thought' | 'tool' | 'tool_complete' | 'error' | 'response' | 'system'
  // Appends to #feed-messages, calls scrollFeed()

function updateFeedStream(chunk) → void
  // Appends chunk to current streaming item (if any)
  // Creates new stream item on first chunk

function finalizeFeedStream() → void
  // Removes pulsing cursor from stream item

function clearFeed() → void
  // Remove all items from #feed-messages

function scrollFeed(force) → void
  // Auto-scroll if within 100px of bottom; else show scroll-to-bottom btn

// Pause/resume (UI only — does not pause Socket.IO)
function toggleFeedPause() → void
  // When paused: buffer incoming items, show "X new events" banner
  // When resumed: flush buffer to DOM
```

## File
- **File**: `index.html` — `#feed-panel` section + `<script>`

## Tasks

### Wave 1 (parallel)

#### Task 1a — Feed panel HTML structure
- **File**: `index.html` — `#feed-panel`
- **touches**: [index.html]
- **provides**: [feed DOM]
- Structure:
  ```
  #feed-panel.panel
    .feed-toolbar
      span "Live Activity"
      div.toolbar-right
        btn#pause-btn  (⏸ / ▶)
        btn#clear-btn  (🗑)
    .feed-messages#feed-messages (scrollable)
    btn.scroll-btn#feed-scroll-btn (↓, shown when scrolled up)
  ```
- Empty state: "A0 is idle" with pulsing green dot

#### Task 1b — Feed CSS
- **File**: `index.html` — `<style>`
- **touches**: [index.html]
- **provides**: [feed item styles, type-specific colors]
- `.feed-item` — base row: timestamp left, icon + text right
- `.feed-item.thought` — dim purple border-left, italic text, `--hint` color
- `.feed-item.tool` — green border-left, tool name bold, args in code block
- `.feed-item.tool_complete` — green border-left, ✓ check, muted text
- `.feed-item.error` — red border-left, red text
- `.feed-item.response` — no border, agent text, markdown rendering
- `.feed-toolbar` — sticky top, flex row, `--hdr-bg` background
- `@keyframes feedIn` — slide-up + fade-in on new item (120ms)
- `.feed-paused-banner` — yellow top banner "Paused — X new events"

### Wave 2 (depends on 1a + 1b)

#### Task 2a — Socket.IO connection + event wiring
- **File**: `index.html` — `<script>`
- **depends_on**: [task-1a]
- **touches**: [index.html]
- **provides**: [connectSocket(), socket global, connection dot updates]
- Connect immediately on app load (not on tab switch — need stream even when on other tabs)
- Auth: `{auth: {handlers: ['webui']}}` — confirmed required by A0
- Events to wire: verify actual event names by logging `socket.onAny()` first
- Connection dot: green=connected, red=disconnected, gray=connecting

#### Task 2b — Feed item renderers
- **File**: `index.html` — `<script>`
- **depends_on**: [task-1a, task-1b]
- **touches**: [index.html]
- **provides**: [addFeedItem(), updateFeedStream(), finalizeFeedStream(), clearFeed()]
- `addFeedItem('thought', {content})` → italic thought row
- `addFeedItem('tool', {tool, emoji, label})` → tool call row with spinner
- `addFeedItem('tool_complete', {tool, result_summary})` → update existing tool row to show ✓
- `addFeedItem('response', ...)` → start streaming row
- Timestamp: `HH:MM:SS` (include seconds for activity feed)
- Max items: 200 (remove oldest when exceeded)

### Wave 3 (depends on 2a + 2b)

#### Task 3a — Pause/resume + scroll button
- **File**: `index.html` — `<script>`
- **depends_on**: [task-2a, task-2b]
- **touches**: [index.html]
- **provides**: [toggleFeedPause(), scrollFeed(), buffered event handling]
- Buffer: `feedBuffer = []` — when paused, push to buffer instead of DOM
- On resume: flush buffer in batches (requestAnimationFrame loop, 20 items/frame)
- Scroll btn: appears when feed scrolled >100px from bottom; click → smooth scroll to bottom
- Haptic: `WebApp?.HapticFeedback?.impactOccurred('light')` on new tool call event

## Failure Scenarios

| When | Then | Error |
|------|------|-------|
| Socket.IO connect fails | Red dot, "Connection failed" in feed | `addFeedItem('system', 'Socket connection failed. Is A0 reachable?')` |
| Socket.IO disconnects mid-session | Auto-reconnect (Socket.IO built-in), yellow dot during reconnect | `addFeedItem('system', 'Reconnecting...')` |
| `agent_error` event | Show error item in feed | Verbatim error from A0 |
| 200+ feed items | Drop oldest | Silent, no notification |
| Event schema differs from plan (wrong field names) | Log raw event, show generic item | `addFeedItem('system', 'Unknown event: <type>')` |
| A0 idle (no events) | Show empty state | "A0 is idle" pulsing dot |

## Rejection Criteria
- DO NOT update DOM inside tight Socket.IO event loop — batch with requestAnimationFrame
- DO NOT disconnect Socket.IO when switching tabs — keep alive for background feed
- DO NOT render raw event JSON in feed — always parse and format
- DO NOT show `agent_thought` content if it's just whitespace
- DO NOT hardcode Socket.IO event names — store in const object at top of script so they're easy to update when verified

```javascript
// Changeable at top of script
const A0_EVENTS = {
  THOUGHT: 'agent_thought',   // VERIFY against live A0
  TOOL: 'agent_tool',         // VERIFY
  RESPONSE: 'agent_response', // VERIFY
  COMPLETE: 'agent_complete', // VERIFY
  ERROR: 'agent_error',       // VERIFY
}
```

## Cross-Phase Context
### Assumes from prior phases
- Phase 1: `baseUrl`, `apiKey`, `api()`, tab switcher, `showApp()`

### Exports for Phase 3+
- `socket` global (reused for any future Socket.IO needs)
- `connectSocket()` (called by Phase 1 init after auth)
- Connection state management (dot in header)

## Acceptance Criteria
- [ ] Feed tab shows real-time tool calls as A0 processes a Telegram message
- [ ] Thoughts render in italic, tools in green, errors in red
- [ ] Pause button stops new items from rendering (buffered)
- [ ] Resume flushes buffer smoothly
- [ ] Auto-scrolls to bottom during active stream
- [ ] Scroll-to-bottom button appears when scrolled up
- [ ] Disconnects reconnect automatically
- [ ] Empty state shown when A0 is idle

## Test Tasks
- Manual: send A0 a complex task via Telegram → watch Feed tab fill in real-time
- Manual: scroll up mid-stream → verify scroll-to-bottom btn appears
- Manual: tap Pause → items buffer → tap Resume → flush visible
- Manual: kill A0 mid-stream → verify reconnect message appears
- Manual: `socket.onAny(console.log)` → verify actual event names from A0

---

## Outcome Block
**What Was Planned**: Phase 2 — Socket.IO activity feed, tool/thought/error items, pause/resume, scroll.

**Immediate Next Action**: Before coding, connect to a running A0 instance and log `socket.onAny()` to confirm real event names. Then `rune:cook` on `feat/phase-2-feed`.

**How to Measure**:
```bash
# Verify Socket.IO connects
# Open browser devtools → Network → WS → connect to A0
# Send a message to the Telegram bot → watch WS frames
# Confirm event names match A0_EVENTS constants
```
