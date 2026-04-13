# Project Contract

Invariants enforced by cook/sentinel. Review and customize.

## Security
- NEVER insert user/API data via `innerHTML` without `esc()` escaping
- NEVER log `initData` or `API_SERVER_KEY` to console
- Auth headers must be injected in the shared `api()` helper — not ad-hoc in callers

## Code Style
- No framework additions — stay Vanilla JS
- No build step — the output is always a single deployable `index.html`
- No `console.log` left in production paths
- Sections delimited by `// ─── SECTION NAME ────` banner comments

## API / Gateway
- All API calls go through the `api(path, opts)` helper
- SSE streaming uses the established pattern in the chat section — don't invent a new one
- Gateway port is 8642 — don't hardcode alternatives

## Deployment
- Final artifact = single `index.html`
- Must work with zero external dependencies beyond `telegram-web-app.js` CDN
