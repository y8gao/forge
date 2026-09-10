---
format: "forge-memory-v1"
mission_id: "simplify-public-interface"
state: "done"
checkpointed_at: "2026-09-09T13:05:25Z"
---
# Current Mission

## Outcome
- Statement: Reduce Forge's advertised user interface to four explicit entrypoints while preserving internal Core, memory, and profile capabilities.

## Scope
- In: Skill invocation metadata, canonical and portable package synchronization, public documentation hierarchy, interface contract tests, and targeted host verification.
- Out: Memory schema changes, runtime routers, capability registries, removal of native profile agents, or changes to the six memory helper protocols.
- Constraints: Implement against Forge v0.2.0; preserve all nine packaged skills; expose only forge-init, forge-status, forge-loop, and forge-assurance to users where the host supports visibility controls.

## Success Criteria
- [x] Exactly four skills are classified and documented as user-invocable public entrypoints.
- [x] Core, Memory, Scout, Builder, and Checker remain model-available but are marked non-user-invocable in every synchronized skill payload.
- [x] Native Scout, Builder, and Checker agents remain packaged, and helper scripts are documented as internal control protocols.
- [x] Contract tests and targeted host/package checks pass with explicit evidence for host visibility limitations.

## Latest Delivery
- Reduced Forge to four advertised user entrypoints while preserving five model-available internal skills, three native profiles, and six internal helper protocols.

## Next Action
- Await explicit authorization before committing or pushing feature/simplify-public-interface.

## Blockers
- None.

## Last Check
- Ran: TDD RED/GREEN contracts passed; 144 integrated interface tests passed; validate-content, portable synchronization, memory validation, and git diff checks passed; full unittest discovery ran 324 tests with 12 skips and zero failures.
- Boundary: Locally verified static contracts and documented Cursor CLI metadata; live Cursor IDE/Cloud, Claude extension menu behavior, Codex skill browser behavior, Command Code, Pi, and DeepSeek Harness invocation surfaces were not exercised.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Await explicit authorization before committing or pushing feature/simplify-public-interface.
