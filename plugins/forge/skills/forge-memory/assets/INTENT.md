---
format: "forge-memory-v1"
---
# Project Intent

## Purpose
- Why: Keep coding agents oriented across sessions.
- User: A developer working with coding agents.

## Direction
- Current: Confirm the first useful outcome for this project.

## Decisions
### D-001: Markdown is canonical control memory
- Decision: Keep active intent and mission in Git-diffable Markdown.
- Rationale: Every supported host can read it directly.
- Status: active

## Constraints
- Only the host agent writes active memory.

## Non-goals
- No runtime hooks, daemon, scheduler, ledger, or external memory provider.
