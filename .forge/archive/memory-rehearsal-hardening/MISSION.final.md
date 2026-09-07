---
format: "forge-memory-v1"
mission_id: "memory-rehearsal-hardening"
state: "done"
checkpointed_at: "2026-09-07T08:36:05Z"
---
# Current Mission

## Outcome
- Statement: Repair Forge Memory publication, timestamp, INTENT boundary, and artifact-lens reliability.

## Scope
- In: Strict Mission timestamp semantics, safe replacement guidance, monotonic checkpoints, durable INTENT separation, canonical lens names, contract tests, portable sync, fresh Cursor rehearsal, and independent Assurance.
- Out: New memory fields, runtime hooks, routers, fixed roles, Cursor CLI automatic registration, Windows OS sandbox support, commits, pushes, real CI, or edits to the approved plan file.
- Constraints: Preserve current schema and helper architecture; use failing tests first; keep every SKILL.md under 500 lines; only the host writes active control memory.

## Success Criteria
- [x] Mission parser, compact, and checkpoint helpers enforce ready/null, strict UTC non-ready timestamps, and no backward checkpoint writes.
- [x] Core and Memory require off-active validated replacement publication and preserve state/timestamp during acceptance-boundary rewrites.
- [x] INTENT remains durable and separate from Mission continuity; canonical artifact lens names remain distinct from capability/action categories.
- [x] Canonical and portable tests pass, and fresh-agent watcher rehearsal plus independent Assurance accept all scoped claims.

## Latest Delivery
- Implemented strict Mission timestamp and safe-publication contracts, durable INTENT isolation, canonical lens taxonomy, synchronized portable payloads, and completed fresh Cursor rehearsal plus independent Assurance.

## Next Action
- Review the ready changes; commit or push only on explicit request.

## Blockers
- None.

## Last Check
- Ran: Full unittest suite: 311 tests OK with 12 expected skips; validate-content, portable sync check, active-memory validation, and git diff --check passed; installed/source plugin hashes matched 45/45; watcher recorded 20/20 valid Mission versions, every replacement ready plus null, monotonic timestamps, stable Direction, and canonical lens outputs; independent Checker accepted all three scoped claims.
- Boundary: Locally verified and independently reviewed, not CI verified. Windows Cursor OS sandbox and automatic CLI discovery remain out of scope. Watcher observed one transient empty INTENT during the authorized durable D-002 update, so atomic INTENT publication is a disclosed follow-up risk outside the frozen content-isolation claim.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Review the ready changes; commit or push only on explicit request.
