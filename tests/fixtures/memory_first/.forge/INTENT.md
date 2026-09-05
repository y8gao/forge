---
format: "forge-memory-v1"
---
# Project Intent

## Purpose
- Why: Help a solo developer keep coding-agent context across sessions.
- User: A solo vibe coder.

## Direction
- Current: Ship a small memory-first plugin.

## Decisions
### D-001: Markdown is canonical control memory
- Decision: Keep active intent and mission in Git-diffable Markdown.
- Rationale: Every supported host can read it directly.
- Status: active

## Constraints
- Temporary agents never write active memory.

## Non-goals
- No daemon, scheduler, ledger, or GraphRAG in the MVP.
