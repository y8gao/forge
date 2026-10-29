---
format: "forge-memory-v1"
mission_id: "claude-mission-guard"
state: "done"
checkpointed_at: "2026-10-29T00:40:12Z"
---
# Current Mission

## Outcome
- Statement: Ship a Claude Code-native PreToolUse guard so substantive Edit/Write calls are refused while the active MISSION is not authorized for work, and the refusal names the exact next step.

## Scope
- In: `plugins/forge/hooks/hooks.json`, `plugins/forge/scripts/forge-guard`, the plugin hook declaration, `tests/test_forge_guard.py`, and a short README note.
- Out: Codex/Cursor equivalents, Bash or sandbox enforcement, version bump, commit, push, release, and any Forge-owned runtime or daemon.
- Constraints: Host-native hook only (D-004 package boundary); reuse `lib/forge_memory.py`; no new dependencies; fail open on missing, unreadable, or unknown Mission data; exempt writes under `.forge/`; block only `done`, `paused`, `blocked`, and `mission_id: initial`.

## Success Criteria
- [x] `hooks/hooks.json` registers PreToolUse for `Edit|Write|MultiEdit|NotebookEdit` through `${CLAUDE_PLUGIN_ROOT}`.
- [x] The guard exits 2 with a state-specific next step for `done`, `paused`, `blocked`, and `mission_id: initial`.
- [x] The guard exits 0 for `ready`, `working`, projects without `.forge`, writes under `.forge/`, and unreadable Mission data.
- [x] `tests/test_forge_guard.py` covers the allow/deny matrix and passes.
- [x] The existing test suite still passes.
- [x] `claude plugin validate plugins/forge` passes.
- [x] A simulated PreToolUse call against a done Mission blocks and a working Mission passes.

## Latest Delivery
- Shipped the Claude Code PreToolUse guard: hooks/hooks.json wires scripts/forge-guard for Edit/Write/MultiEdit/NotebookEdit; the guard reuses load_mission, blocks done/paused/blocked/mission_id initial, exempts .forge/ writes, and fails open; 13 focused tests pass; claude plugin validate plugins/forge passes.

## Next Action
- The workspace change is complete and validated; decide whether to bump the version and install it. The installed 0.3.0 cache still has no hook, so existing sessions are not guarded yet.

## Blockers
- None.

## Last Check
- Ran: python3 -m unittest tests.test_forge_guard -v (13 passed); full suite on macOS (339 tests, 6 pre-existing test_release failures from bash 3.2 mapfile, reproduced on the clean 0.3.0 clone); Linux Python 3.12 container non-release suite (315 passed, 3 skipped); python3 scripts/validate-content.py PASS; claude plugin validate plugins/forge PASS; simulated PreToolUse payloads: done exit 2, .forge write and ready exit 0.
- Boundary: Hook wiring was validated by manifest validation and simulated stdin payloads; no live Claude Code session ran with the modified plugin, and the installed 0.3.0 cache does not include it. No version bump, commit, or push.

## Resume
- Read: `.forge/INTENT.md`, `.forge/MISSION.md`, `plugins/forge/lib/forge_memory.py`.
- Do: The workspace change is complete and validated; decide whether to bump the version and install it. The installed 0.3.0 cache still has no hook, so existing sessions are not guarded yet.
