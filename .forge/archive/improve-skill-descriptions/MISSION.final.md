---
format: "forge-memory-v1"
mission_id: "improve-skill-descriptions"
state: "done"
checkpointed_at: "2026-09-10T02:04:09Z"
---
# Current Mission

## Outcome
- Statement: Make all nine Forge skill descriptions follow discovery best practices with precise trigger-only wording.

## Scope
- In: Canonical SKILL.md descriptions, exact description contracts, portable synchronization, and targeted/full regression checks.
- Out: Skill names, invocation visibility, Skill bodies, native agent definitions, memory schemas, or helper behavior.
- Constraints: Each description starts with `Use when`, states concrete invocation conditions without summarizing workflow, and remains synchronized across all packaged payloads.

## Success Criteria
- [x] All nine canonical descriptions use trigger-only `Use when` wording with clear boundaries.
- [x] Existing exact frontmatter contracts use the new descriptions without weakening invocation metadata checks.
- [x] Portable Agent Skills and DeepSeek Harness payloads exactly match canonical descriptions.
- [x] Targeted description/interface tests, validators, and the full local suite pass.

## Latest Delivery
- Rewrote all nine Forge skill descriptions as precise trigger-only Use when conditions and synchronized every portable payload.

## Next Action
- Await explicit authorization before committing or pushing feature/simplify-public-interface.

## Blockers
- None.

## Last Check
- Ran: Observed 13 expected RED failures before description edits; canonical 78-test GREEN passed; portable 6-test sync suite passed; integrated 166 tests and all validators passed; full discovery ran 325 tests with 12 skips and zero failures.
- Boundary: Locally verified description bytes, metadata contracts, portable mirrors, and repository regressions; live host discovery and invocation behavior was not exercised.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Await explicit authorization before committing or pushing feature/simplify-public-interface.
