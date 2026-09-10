---
format: "forge-memory-v1"
mission_id: "refine-and-rehearse-skill-interface"
state: "done"
checkpointed_at: "2026-09-10T03:11:56Z"
---
# Current Mission

## Outcome
- Statement: Remove remaining skill-description overlap and test duplication, then verify the four-command interface with the installed Cursor CLI.

## Scope
- In: Four canonical descriptions, description contract ownership, synchronized payloads, local regression checks, and one read-only Cursor CLI rehearsal using the local plugin.
- Out: Skill bodies, invocation metadata, agent definitions, memory schemas, commits, pushes, or fixes for host-runtime limitations.
- Constraints: Keep exact description copy in one test module; preserve four public and five internal skills; use installed Cursor Agent 2026.05.09 without repository write authority.

## Success Criteria
- [x] Core, Memory, Builder, and Checker descriptions have non-overlapping trigger-only conditions.
- [x] Exact description strings are owned only by the dedicated skill-interface contract.
- [x] Canonical and portable payloads remain exact mirrors and the full local suite passes.
- [x] A local Cursor CLI rehearsal records whether only the four public skills resolve as slash commands, with unsupported surfaces reported explicitly.

## Latest Delivery
- Removed remaining description overlap, centralized exact description ownership, synchronized portable payloads, and rehearsed slash resolution with the installed Cursor CLI.

## Next Action
- Optionally update Cursor Agent and repeat the live slash-visibility rehearsal, or authorize committing feature/simplify-public-interface.

## Blockers
- None.

## Last Check
- Ran: Observed 4 expected RED description failures; 79 targeted contracts passed; portable 6-test suite and all validators passed; full discovery ran 326 tests with 12 skips and zero failures; Cursor Agent 2026.05.09 loaded the local plugin and resolved both /forge-status and hidden /forge-core.
- Boundary: The installed pre-July Cursor CLI exposed all nine skills, so four-command hiding is not live-verified on a supporting CLI version; updating the user-installed CLI was outside this task, and IDE/Cloud/other-host menus remain unchecked.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Optionally update Cursor Agent and repeat the live slash-visibility rehearsal, or authorize committing feature/simplify-public-interface.
