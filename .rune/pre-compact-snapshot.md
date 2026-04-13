# Pre-Compact Snapshot
Generated: 2026-04-13T01:22:09.725Z

## Session Metrics
- Tool calls: 27
- Session start: 2026-04-13T00:16:05.636Z
- Top tools: Edit(22), Write(5)

## State Files (preview)
### .rune/progress.md
# Progress Log

- 2026-04-12: Project onboarded. Reference implementation scanned. CLAUDE.md + .rune/ initialized.
- 2026-04-12: Phase 1 complete — commit 236b0e9 on feat/phase-1-scaffold. All 10 auth unit tests green.
- 2026-04-12: Phase 2 complete — Feed tab, Socket.IO activity stream, pause/resume buffer.
- 2026-04-12: Phase 3 complete — Config tab, LLM switcher, plugin toggles, reset. Merged to main.
- 2026-04-12: Phase 4 complete — Manage tab, chats, scheduler, tunnel widget. PR#4 open.
- 2026-04-12: Phase 5 complete — Shell tab, shell.py full impl, visual polish, README, v0.1.0. PR#5 open.

### .rune/decisions.md
# Architecture Decisions

| Date | Decision | Rationale | Status |
|------|----------|-----------|--------|
| — | — | — | — |

### .rune/conventions.md
# Project Conventions

Detected from `Reference/hermes-telegram-miniapp/index.html` (2026-04-12).

## Architecture
- **Single-file SPA**: all HTML, CSS, JS in one `index.html` — no build step, no bundler
- Deploy = copy file to `~/.hermes/miniapp/index.html`
- ~75KB total; inline `<style>` + inline `<script>` blocks

## JS Naming
- Functions: camelCase (`loadStatus`, `persistSession`, `addMsg`)
- Variables: camelCase (`sessionId`, `streamDiv`, `firstChunk`)
- Private/module-level globals: underscore prefix (`_streamDiv`, `_typing`)
- Constants: ALL_CAPS not used — camelCase even for constants

## CSS Naming
- Classes: kebab-case (`menu-drawer`, `drawer-overlay`, `cmd-item`, `status-chip`)
- IDs: kebab-case (`status-bar`, `status-content`)
- CSS vars: `--tg-theme-*` for Telegram palette tokens; local aliases (`--bg`, `--text`, `--hint`, `--btn`)

## Error Handling
- Non-critical paths: silent swallow `catch (_) {}`
- API calls: `try/catch` wrapping `async` functions; fall back to null/empty state
- `Promise.allSettled` for parallel calls where partial failure is acceptable

## API Pattern
- REST: `async function api(path, opts)` helper — auto-injects auth headers
- Streaming: SSE via `EventSource` or `fetch` + ReadableStream on `/v1/chat/completions`
- Auth: `X-Telegram-Init-Data` header (primary) → `Authorization: Bearer <API_SERVER_KEY>` (fallback)

## DOM / Rendering
- Template strings for HTML generation (no framework, no virtual DOM)
- `innerHTML` assignment for bulk updates; `textContent` for user-controlled strings (XSS safety)
- `esc()` helper used for escaping user/API data before innerHTML insertion

## State
- Global JS vars at module level (no Redux, no Zustand, no signals)
- `CloudStorage` (Telegram SDK) for persistence: `CS.setItem/getItem`
- `localStorage` as fallback when CS unavailable

## UI Sections (Tabs)
Three main tabs: **Chat**, **Status**, **Cron** — rendered via tab-switch logic, not routing

## File/Section Organization
Sections delimited by banner comments: `// ─── SECTION NAME ──────────`
