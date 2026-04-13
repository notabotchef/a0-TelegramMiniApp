# Phase 3: Config Tab — LLM Switcher + Plugin Manager + Reset

## Goal
Control A0 from Telegram: switch the active LLM model, toggle plugins on/off, reset/nudge the agent.

## Data Flow

### Config tab load
```
Tab activated
  ↓
Promise.allSettled([
  POST /api/plugins/_model_config/model_config_get → current model config
  POST /api/plugins_list → all available plugins
  POST /api/plugins {action: "get_toggle_status", plugin_name: each} → enabled state
])
  ↓
Render: model section + plugin cards grid
```

### Switch model
```
User selects model from picker
  ↓
POST /api/plugins/_model_config/model_config_set
  {config: {chat_model: {provider, name, ...existing}}}
  ↓ success
Toast "Model updated" + refresh display
```

### Toggle plugin
```
User taps toggle on plugin card
  ↓
POST /api/plugins {action: "toggle_plugin", plugin_name, enabled: !current}
  ↓ success
Update toggle state, toast
```

### Reset agent
```
User taps Reset → confirmation dialog (native Telegram popup)
  ↓ confirmed
POST /api/nudge {ctxid: currentContextId || ""}
  ↓ success
Toast "Agent reset"
```

## Code Contracts

```javascript
// Config state
let currentModelConfig = null   // full model_config_get response
let pluginList = []             // [{name, label, enabled, description}]

// Load
async function loadConfigTab() → void
  // Parallel fetch model + plugins, render both sections

// Model
async function loadModelConfig() → {provider, name, ctx_length, ...}
async function setModel(provider, name) → void
  // POST model_config_set with minimal delta (provider + name only)
  // Keep all other fields from currentModelConfig

// Plugins
async function loadPlugins() → Plugin[]
async function togglePlugin(name, enable) → void
  // POST /api/plugins {action: "toggle_plugin", plugin_name: name, enabled: enable}

// Reset
async function resetAgent() → void
  // WebApp.showConfirm("Reset Agent Zero? Current tasks will be interrupted.", cb)
  // On confirm: POST /api/nudge

// UI helpers
function renderModelSection(config) → void
function renderPluginCards(plugins) → void
```

## File
- **File**: `index.html` — `#config-panel` section + `<script>`

## Tasks

### Wave 1 (parallel)

#### Task 1a — Config panel HTML
- **File**: `index.html` — `#config-panel`
- **touches**: [index.html]
- **provides**: [config DOM structure]
- Structure:
  ```
  #config-panel.panel
    .panel-scroll
      .section#model-section
        .section-header "LLM Model"
        .model-current  (current provider/model name display)
        .model-picker   (scrollable chip list of preset models)
        
      .section#plugins-section
        .section-header "Plugins" + badge(count)
        .plugin-grid    (cards, 2-col grid)
        
      .section#danger-section
        .section-header "Agent"
        button#reset-btn "Reset Agent" (red, full width)
  ```

#### Task 1b — Config CSS
- **File**: `index.html` — `<style>`
- **touches**: [index.html]
- **provides**: [model picker, plugin card, toggle styles]
- `.model-current` — large text: `Provider / model-name`, subtitle: context length
- `.model-chip` — pill button, accent border when selected
- `.plugin-card` — card with icon + name + description + toggle right side
- `.toggle` — iOS-style toggle switch (CSS only, no JS library)
  - `.toggle input[type=checkbox]` hidden, label styled as track+thumb
  - On = `--accent` green; Off = `--hint` gray
- `.reset-btn` — full-width, red, large tap target
- Loading skeleton: pulse animation on model section + plugin cards

### Wave 2 (depends on 1a + 1b)

#### Task 2a — Model config fetch + render
- **File**: `index.html` — `<script>`
- **depends_on**: [task-1a]
- **touches**: [index.html]
- **provides**: [loadModelConfig(), renderModelSection(), setModel()]
- `loadModelConfig()`: POST `/api/plugins/_model_config/model_config_get` → store in `currentModelConfig`
- `renderModelSection()`: show current `chat_model.provider / chat_model.name`, context length
- Model presets: hardcode common ones (OpenAI gpt-4o, Claude Sonnet, Gemini Pro, Ollama llama3) + "Custom" option
- `setModel()`: POST `model_config_set` with `{config: {...currentModelConfig.config, chat_model: {...currentModelConfig.config.chat_model, provider, name}}}`
- If `_model_config` plugin returns 404: show "Model Config plugin not installed" graceful state

#### Task 2b — Plugin list fetch + render + toggle
- **File**: `index.html` — `<script>`
- **depends_on**: [task-1a]
- **touches**: [index.html]
- **provides**: [loadPlugins(), renderPluginCards(), togglePlugin()]
- `loadPlugins()`: POST `/api/plugins_list` → iterate, POST `get_toggle_status` for each
- Filter: don't show `_miniapp` (ourselves) or `_model_config` (has dedicated section)
- `renderPluginCards()`: each card = icon emoji + name + short description + toggle
- `togglePlugin()`: optimistic UI update → POST toggle_plugin → revert on error + toast

### Wave 3 (depends on 2a + 2b)

#### Task 3a — Reset button + loadConfigTab()
- **File**: `index.html` — `<script>`
- **depends_on**: [task-2a, task-2b]
- **touches**: [index.html]
- **provides**: [resetAgent(), loadConfigTab()]
- `loadConfigTab()`: `Promise.allSettled([loadModelConfig(), loadPlugins()])` → render both
- Called on Config tab activate (lazy load — only when tab first opened)
- Cache: don't reload if already loaded and < 60s old
- `resetAgent()`: `WebApp.showConfirm(...)` → POST /api/nudge → toast "Agent reset ✓"

## Failure Scenarios

| When | Then | Error |
|------|------|-------|
| `_model_config` plugin not installed | Show placeholder "Model Config plugin not available" | Gray state, no crash |
| `plugins_list` returns empty | Show "No plugins found" | Gray empty state |
| `toggle_plugin` fails | Revert toggle UI, toast error | "Failed to toggle <name>" |
| `model_config_set` fails | Keep old config, toast error | "Model update failed: <reason>" |
| `/api/nudge` fails | Toast error | "Reset failed. Try again." |
| Too many plugins (>20) | Show first 20, "+ N more" | Prevent layout overflow |

## Rejection Criteria
- DO NOT show API keys in model config display
- DO NOT allow toggling `_telegram_integration` off (would break auth) — hide it
- DO NOT reload plugin list on every tab switch — cache with 60s TTL
- DO NOT use native `confirm()` — use `WebApp.showConfirm()` for Telegram-native dialog
- DO NOT send full model config on setModel — only update the fields that changed

## Cross-Phase Context
### Assumes from prior phases
- Phase 1: `api()`, `baseUrl`, `apiKey`, tab switcher, CSS vars
- Phase 2: Socket.IO connected (no dependency, but socket already exists)

### Exports for Phase 4
- Nothing specific — Phase 4 uses same `api()` pattern independently

## Acceptance Criteria
- [ ] Config tab shows current model (provider/name/context length)
- [ ] Tapping a model chip → POST to A0 → toast confirmation
- [ ] Plugin cards render with correct enabled/disabled state
- [ ] Toggling plugin → instant optimistic UI → confirmed by API
- [ ] Reset button → Telegram native confirm dialog → POST nudge → toast
- [ ] If `_model_config` not installed → graceful message, no crash
- [ ] Tab caches data for 60s (no refetch on every switch)

## Test Tasks
- Manual: open Config tab → verify current model shows
- Manual: tap different model chip → verify POST sent → toast shown
- Manual: toggle a plugin off → verify card updates → toggle back on
- Manual: tap Reset → confirm dialog appears → confirm → toast "Agent reset ✓"
- Manual: open Config with no _model_config plugin → verify graceful state

---

## Outcome Block
**What Was Planned**: Phase 3 — LLM switcher, plugin toggle cards, agent reset.

**Immediate Next Action**: `rune:cook` on `feat/phase-3-config`.

**How to Measure**:
```bash
# Verify model config endpoint
curl -X POST http://localhost:50080/api/plugins/_model_config/model_config_get \
  -H "X-API-KEY: <key>" -H "Content-Type: application/json" -d '{}'

# Verify plugins list
curl -X POST http://localhost:50080/api/plugins_list \
  -H "X-API-KEY: <key>" -H "Content-Type: application/json" -d '{}'
```
