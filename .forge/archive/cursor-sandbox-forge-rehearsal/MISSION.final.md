---
format: "forge-memory-v1"
mission_id: "cursor-sandbox-forge-rehearsal"
state: "blocked"
checkpointed_at: "2026-09-07T07:25:20Z"
---
# Current Mission

## Outcome
- Statement: Install the current Forge build into Cursor and rehearse its complete workflow in isolated sandboxes.

## Scope
- In: Current Cursor plugin installation, isolated sandbox scenarios, init and Mission lifecycle, Core delivery, explicit Loop and Assurance, artifact lenses, capability selection, checkpoints, completion, and resume inspection.
- Out: Production deployment, unrelated Cursor settings, changes to the approved artifact-reasoning plan, and claims about external hosts or real CI.
- Constraints: Keep rehearsal artifacts outside the Forge repository, preserve user content, use only host-owned active-memory writes, and report exact evidence and gaps.

## Success Criteria
- [x] The installed Cursor Forge package matches the current repository build and is visible to fresh Cursor agents.
- [x] Sandbox runs exercise initialization, Mission activation, visible delivery, bugfix continuation, explicit Loop, explicit Assurance, completion, and resume behavior.
- [ ] `.forge/INTENT.md` and `.forge/MISSION.md` update only at the expected real transitions and validate after each write.
- [ ] The new reasoning kernel selects appropriate primary/supporting artifact lenses and minimum host capabilities without fixed roles or automatic modes.

## Latest Delivery
- Completed the Cursor rehearsal and published a standalone evidence review covering installation, six workflow scenarios, 20 observed Mission versions, capability/lens use, and reproducible gaps.

## Next Action
- Decide whether to repair the observed safe-publication, timestamp, Intent-boundary, lens-label, and Cursor CLI discovery gaps.

## Blockers
- Replacement Missions were published invalid before validation in Loop and bugfix scenarios.
- Agents invented future checkpoint timestamps, followed by earlier helper-generated completion timestamps.
- INTENT Direction was rewritten with per-Mission and pause/completion state that belongs in MISSION.
- Loop cycle 1 reported the action category Implementation as the primary lens instead of the canonical Code lens.

## Last Check
- Ran: Installed/source SHA maps matched for 45 files; sandbox final suite ran 23 tests OK; final memory validation passed; watcher captured 20 Mission versions, including 3 invalid visible snapshots and 2 backward timestamp sequences; Canvas TypeScript check reported no errors.
- Boundary: Fresh agents with explicit --plugin-dir exercised current Forge. Windows lacks Cursor OS sandbox, so isolation was a separate git workspace; without --plugin-dir the fresh CLI did not register Forge Skills; Desktop reload and external hosts remain unchecked.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Decide whether to repair the observed safe-publication, timestamp, Intent-boundary, lens-label, and Cursor CLI discovery gaps.
