---
format: "forge-memory-v1"
mission_id: "atomic-intent-publication"
state: "done"
checkpointed_at: "2026-09-07T09:18:22Z"
---
# Current Mission

## Outcome
- Statement: Ensure every supported INTENT update is prevalidated and atomically published.

## Scope
- In: A minimal INTENT replacement helper, Memory guidance, portable synchronization, regression tests, and fresh watcher validation.
- Out: Schema changes, multi-user locking, Mission behavior changes, runtime hooks, commits, pushes, real CI, Cursor automatic discovery, or Windows OS sandbox support.
- Constraints: Reuse shared atomic-write semantics; preserve the current INTENT schema and host-only authority; add no daemon or control plane.

## Success Criteria
- [x] Invalid replacement INTENT bytes fail before any active write and valid replacements preserve exact validated bytes.
- [x] INTENT publication uses same-directory atomic replacement and leaves no temporary file on success or failure.
- [x] Forge guidance directs durable INTENT updates through the supported helper while routine checkpoints remain MISSION-only.
- [x] Targeted and full tests, portable checks, and a fresh watcher rehearsal pass without a transient invalid INTENT version.

## Latest Delivery
- Added forge-intent for prevalidated atomic INTENT publication, wired it into Memory guidance and portable payloads, and verified the real fresh-agent path with a 1ms watcher.

## Next Action
- Review the ready changes; commit or push only on explicit request.

## Blockers
- None.

## Last Check
- Ran: Four forge-intent tests passed after confirmed RED failures; full unittest suite ran 317 tests OK with 12 expected skips; sync, content, active-memory, and diff checks passed; installed/source hashes matched 47/47; fresh watcher observed exactly two valid INTENT versions and no empty or partial state.
- Boundary: Locally verified on Windows with explicit Cursor --plugin-dir and an isolated Git workspace; no real CI, Windows OS sandbox, automatic CLI discovery, commit, or push.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Review the ready changes; commit or push only on explicit request.
