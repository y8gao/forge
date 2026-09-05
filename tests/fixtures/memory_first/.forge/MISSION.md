---
format: "forge-memory-v1"
mission_id: "memory-first-fixture"
state: "working"
checkpointed_at: "2026-09-01T12:00:00Z"
---
# Current Mission

## Outcome
- Statement: Implement the memory validator.

## Scope
- In: Parser and template.
- In: Checkpoint renderer.
- Out: Runtime workflow engine.
- Constraints: Keep MISSION within 60 lines.

## Success Criteria
- [ ] Parser accepts the new schema.
- [x] Checkpoint preserves frozen criteria.

## Latest Delivery
- Added canonical memory fixtures.

## Next Action
- Implement validation against the fixtures.

## Blockers
- None.

## Last Check
- Ran: `python -m unittest tests.test_memory_contract -v`
- Boundary: The validator implementation does not exist yet.

## Resume
- Read: `plugins/forge/lib/forge_memory.py`
- Do: implement `load_intent` and `load_mission`.
