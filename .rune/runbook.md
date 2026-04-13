# .rune/runbook.md

## Goal
Build the Agent Zero Telegram Mini App v0.1 — a 4-tab control panel (Feed, Config, Manage, Shell) living inside Telegram. Single-file SPA (`index.html`) with no build step. Connects to Agent Zero via Socket.IO + REST. Auth via Telegram initData HMAC-SHA256 through a Python plugin we ship.

## Plan
plan-a0-miniapp.md

## Quality Rules
- max_severity: MEDIUM        # highest severity allowed to pass (autopilot blocks on HIGH+)
- require_new_tests: false    # no automated test framework — manual tests only
- coverage_floor: none        # no automated coverage tooling
- e2e_on_complete: false      # no automated E2E — manual verification steps in each phase

## Escalation
- on_blocked: pause           # pause | report | retry
- warn_threshold: 5           # pause after N accumulated WARNs across phases (relaxed for UI-heavy project)
- max_retries_per_phase: 2    # max fix attempts before BLOCKED

## Session Strategy
- phases_per_session: auto    # auto = fit as many as context allows
- commit_per_phase: true      # commit after each phase

## Completion Criteria
- all_phases_complete: true
- e2e_pass: false             # manual only
- final_review_clean: true

## Notes
- No automated test framework — "test_count" in baseline snapshots will be 0; this is expected
- No linter configured — lint checks will be skipped
- No type checker — TypeScript not used
- Baseline "healthy" for this project = no broken build (single HTML file, no build step)
- Regression check = verify index.html is well-formed HTML after each phase
- A0 plugin files (Python) are standalone and testable manually only
