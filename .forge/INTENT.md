---
format: "forge-memory-v1"
---
# Project Intent

## Purpose
- Why: Keep coding agents oriented across sessions so useful project work can continue without repeated context reconstruction.
- User: Solo developers using coding agents on long-running projects across Claude Code, Codex, or Cursor.

## Direction
- Current: Keep coding agents oriented across sessions with small active Memory-First control memory, then help them continue useful work.

## Decisions
### D-001: Memory-First is current product authority
- Decision: The checked-in Memory-First skills, helpers, native package manifests, and active control-memory schema are current product authority.
- Rationale: Continuity for solo developers is the primary outcome, so the product stays focused on small explicit memory and useful host-native execution.
- Status: active

### D-002: Markdown is canonical active control memory
- Decision: `.forge/INTENT.md` and `.forge/MISSION.md` are the only control-memory files kept in the active project tree.
- Rationale: Human-reviewable, Git-diffable files provide deterministic cross-session orientation without a database-backed runtime.
- Status: active

### D-003: Core is lightweight and optional capabilities are explicit
- Decision: The host executes ordinary work directly in Core; Loop and Assurance require explicit user invocation, and temporary capability profiles are selected only when useful for the task.
- Rationale: Delivery effort should scale with the task instead of simulating a permanent role organization or automatic gate pipeline.
- Status: active

### D-004: Supported hosts share one thin product core
- Decision: Claude Code, Codex, and Cursor ship as profile-equivalent native packages; Command Code, Pi Coding Agent, and DeepSeek Harness receive the same Memory-First Core skills without a profile-equivalence guarantee.
- Rationale: Host-native delivery preserves portability while capability claims remain limited to permission isolation each host can actually enforce.
- Status: active

### D-005: Public product history starts from the current product
- Decision: The public Forge repository starts from a clean current-product snapshot; private development history remains separate.
- Rationale: First-release users should see one coherent Memory-First product history without importing unrelated experiments.
- Status: active

## Constraints
- Only the host agent writes active control memory.
- Support Claude Code, Codex, Cursor, Command Code, Pi Coding Agent, and DeepSeek Harness with shared Core semantics.
- Keep each `SKILL.md` under 500 lines and Markdown templates parser-friendly.
- Report targeted checks and evidence boundaries honestly.

## Non-goals
- No daemon, scheduler, ledger, locks, or database-backed control plane.
- No fixed permanent-role workflow or automatic Assurance.
- No embedded external recall provider, multi-user synchronization, or automated CI deployment.
