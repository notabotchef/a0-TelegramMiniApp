# Phase 5: Shell Tab + Polish + v0.1.0 Release

## Goal
Direct shell access to A0's Docker container. Final UI polish. Full README. GitHub release v0.1.0.

## Shell Tab Data Flow
```
User types command + taps Run
  ↓
POST <baseUrl>/api/plugins/_miniapp/shell
  {cmd: "ls -la", context_id: "shell-<userId>"}
  X-API-KEY: apiKey
  ↓
socket.io event: shell_output chunks arrive (or response JSON)
  ↓
Render in terminal-style output box (monospace, dark bg)
Streaming output if Socket.IO; full output if sync response
  ↓
Keep last 500 lines of output; prompt stays at bottom
```

## Shell Plugin Data Flow (Python)
```
POST /api/plugins/_miniapp/shell
  {cmd: str, context_id: str}
  ↓
Validate: cmd not empty, context_id format ok
  ↓
subprocess.run(cmd, shell=True, capture_output=True,
               timeout=30, cwd="/a0",
               env={**os.environ, "TERM":"xterm"})
  ↓
Return: {stdout, stderr, exit_code, duration_ms}
  (sync, max 30s — long-running commands show timeout error)
```

## Code Contracts

### Python

```python
# a0-plugin/_miniapp/api/shell.py (implements Phase 1 stub)
# POST /api/plugins/_miniapp/shell
# Auth: requires X-API-KEY (standard A0 auth)
# Input: {cmd: str}
# Output: {stdout: str, stderr: str, exit_code: int, duration_ms: int}
# Timeout: 30s
# Max output: 50KB (truncate with notice)
# Blocked: rm -rf /, format, shutdown, reboot (safety list)
```

### JavaScript

```javascript
// Shell state
let shellHistory = []       // command history (up arrow)
let shellHistoryIdx = -1
let shellLines = []         // rendered output lines (max 500)

// Run command
async function runShell(cmd) → void
  // POST api/plugins/_miniapp/shell {cmd}
  // On success: append stdout/stderr to #shell-output
  // On error: append error line in red
  // Save to shellHistory

// History navigation
function shellKeydown(e) → void
  // ArrowUp: recall previous command
  // ArrowDown: recall next command / clear
  // Enter: runShell(input.value)

// Output rendering
function appendShellOutput(stdout, stderr, exit_code) → void
  // stdout lines: white
  // stderr lines: yellow (warnings) or red (errors based on exit_code)
  // exit_code != 0: show "exit <code>" in red
  // Trim shellLines to 500

function clearShell() → void
function scrollShellToBottom() → void
```

## File
- **File**: `index.html` — `#shell-panel` section + `<script>`
- **File**: `a0-plugin/_miniapp/api/shell.py` — implements Phase 1 stub

## Tasks

### Wave 1 (parallel)

#### Task 1a — Shell plugin `shell.py` (full implementation)
- **File**: `a0-plugin/_miniapp/api/shell.py`
- **touches**: [a0-plugin/_miniapp/api/shell.py]
- **provides**: [POST /api/plugins/_miniapp/shell]
- Use `subprocess.run` with `shell=True`, `capture_output=True`, `timeout=30`, `cwd="/a0"`
- Blocklist: `["rm -rf /", ":(){ :|:& };:", "mkfs", "dd if=", "shutdown", "reboot", "halt"]`
- If cmd contains blocklist item → return `{error: "Command blocked for safety", exit_code: -1}`
- Truncate stdout+stderr combined at 50_000 chars, append `\n[output truncated]`
- Requires: X-API-KEY auth (standard — NOT skip_auth like auth.py)
- Return: `{stdout, stderr, exit_code, duration_ms}`

#### Task 1b — Shell panel HTML + CSS
- **File**: `index.html` — `#shell-panel`
- **touches**: [index.html]
- **provides**: [shell terminal UI]
- Structure:
  ```
  #shell-panel.panel
    .shell-header
      span.shell-cwd "/a0"  (static for now)
      btn.clear-btn "Clear"
    .shell-output#shell-output  (scrollable, monospace, dark bg)
    .shell-input-bar
      span.shell-prompt "$ "
      input#shell-input (no autocorrect, no autocapitalize)
      btn#shell-run "↵"
  ```
- Font: monospace stack (inherit)
- `#shell-output`: `background: #050505`, `color: #d4d4d4`, `padding: 12px`, `font-size: 12px`
- `.shell-line.stderr`: `color: #fbbf24` (yellow)
- `.shell-line.error-exit`: `color: #ef4444` (red)
- `.shell-prompt`: `color: var(--accent)` (green $)
- `input#shell-input`: transparent bg, no border, `color: #d4d4d4`, `caret-color: var(--accent)`

### Wave 2 (depends on 1a + 1b)

#### Task 2a — Shell execution + history
- **File**: `index.html` — `<script>`
- **depends_on**: [task-1a, task-1b]
- **touches**: [index.html]
- **provides**: [runShell(), shellKeydown(), appendShellOutput(), clearShell()]
- Loading state: append `$ <cmd>` line immediately, then spinner line `...`
- On response: remove spinner, render stdout/stderr
- History: `shellHistory` array, max 50 entries, arrow keys navigate
- Auto-focus `#shell-input` when Shell tab activated

### Wave 3 (depends on 2a, parallel)

#### Task 3a — Visual polish pass
- **File**: `index.html`
- **depends_on**: [task-2a]
- **touches**: [index.html]
- **provides**: [final UI polish]
- Empty states: each tab has meaningful empty state (not blank)
  - Feed: pulsing green dot "Waiting for activity..."
  - Config: loading skeletons on cards
  - Manage: "No conversations yet" / "No tasks scheduled"
  - Shell: welcome line `Agent Zero Shell v0.1 — type help for commands`
- Animations: 120ms fade+slide on all new list items
- Keyboard: visualViewport handler (copy from Hermes ref) for input bar offset
- Safe areas: `padding-bottom: var(--safe-bottom)` on input bars
- Header polish: gradient separator line, icon alignment
- Tab bar: active tab has `--accent` underline + slightly brighter icon

#### Task 3b — README.md (complete)
- **File**: `README.md`
- **touches**: [README.md]
- **provides**: [complete user-facing docs]
- Sections: What it is · Prerequisites · Setup (copy-paste steps) · Docker config · Tunnel setup · Troubleshooting · Contributing
- Key: ALLOWED_ORIGINS env var, docker-compose volume mount for plugin, BotFather Mini App URL

#### Task 3c — Version + release
- **File**: `index.html` meta, GitHub
- **touches**: [index.html]
- **provides**: [v0.1.0 release]
- `<meta name="version" content="0.1.0">`
- Settings modal footer: "v0.1.0 · notabotchef/agent-zero-telegram-miniapp"
- Git tag `v0.1.0`, GitHub release with `index.html` + `a0-plugin/` zip as assets

## Failure Scenarios

| When | Then | Error |
|------|------|-------|
| Shell command times out (30s) | Return timeout error | "Command timed out after 30s" |
| Blocked command attempted | Return blocked error | "Command blocked for safety" |
| Subprocess not available in A0 Docker | Return 500 | "Shell not available. Check Docker setup." |
| Output > 50KB | Truncate | "[output truncated at 50KB]" appended |
| Exit code non-zero | Show exit code in red | "exit 1" line at end |

## Rejection Criteria
- DO NOT allow arbitrary `rm -rf` variants — blocklist applies
- DO NOT add autocorrect/autocapitalize to shell input — it ruins commands
- DO NOT show a "build step required" message — the file MUST stay single-file
- DO NOT import any npm packages — CDN-only external deps (Socket.IO + Telegram SDK)
- DO NOT release without testing shell on a real A0 Docker instance

## Cross-Phase Context
### Assumes from prior phases
- All phases complete
- Phase 1: `_miniapp` plugin directory, auth, `api()` helper
- Phase 2: Socket.IO, CSS vars
- Phase 3: Section/card CSS patterns

## Acceptance Criteria
- [ ] Shell tab: type `ls`, press Enter → directory listing appears
- [ ] stderr renders in yellow, non-zero exit in red
- [ ] Arrow up/down navigates command history
- [ ] Shell blocked commands return friendly error (no server crash)
- [ ] `index.html` < 120KB
- [ ] Keyboard does not cover shell input on mobile
- [ ] README: copy-paste setup works end-to-end
- [ ] GitHub release `v0.1.0` with assets

## Test Tasks
- Manual: `ls -la /a0` → verify output renders correctly
- Manual: `python3 --version` → verify Python version shows
- Manual: attempt `rm -rf /` → verify blocked error
- Manual: run `sleep 35` → verify timeout error after 30s
- Manual: keyboard on iOS/Android → verify input bar not covered

---

## Outcome Block
**What Was Planned**: Phase 5 — shell tab + `shell.py` plugin, UI polish, README, v0.1.0 release.

**Immediate Next Action**: `rune:cook` on `feat/phase-5-shell-polish` after Phase 4 PR merged.

**How to Measure**:
```bash
# Final artifact sizes
wc -c index.html          # < 120,000 bytes
wc -l index.html          # informational
ls -la a0-plugin/         # plugin files present

# Shell endpoint
curl -X POST http://localhost:50080/api/plugins/_miniapp/shell \
  -H "X-API-KEY: <key>" -H "Content-Type: application/json" \
  -d '{"cmd": "echo hello"}'
# Expected: {"stdout": "hello\n", "stderr": "", "exit_code": 0}

# Release
gh release view v0.1.0
```
