---
format: "forge-memory-v1"
mission_id: "three-host-core-support"
state: "done"
checkpointed_at: "2026-09-07T01:48:20Z"
---
# Current Mission

## Outcome
- Statement: Add Core-level Forge delivery for Command Code, Pi Coding Agent, and DeepSeek Harness through each host's official package mechanism.

## Scope
- In: Portable Agent Skills payload, Command Code skill installation, Pi package metadata, experimental DeepSeek Harness bundle, tier-aware capability metadata, release synchronization, CI smoke checks, and public documentation.
- Out: Full Scout/Builder/Checker permission-profile equivalence on the three new hosts, publishing packages, committing, or pushing.
- Constraints: Preserve Claude Code, Codex, and Cursor behavior; keep every `SKILL.md` under 500 lines; pin PR compatibility checks and report experimental boundaries honestly.

## Success Criteria
- [x] All nine Forge skills are installable through a synchronized portable Agent Skills payload.
- [x] Command Code and Pi use their documented skill/package discovery mechanisms.
- [x] DeepSeek Harness has a pinned experimental DSH bundle that registers all nine skills with resource bases.
- [x] Capability metadata and documentation distinguish profile-equivalent native hosts from Core-level hosts.
- [x] Release tooling synchronizes all versioned package manifests without weakening its receipt boundary.
- [x] Targeted package checks and the full local test suite pass.

## Latest Delivery
- Implemented and verified portable Core support for Command Code, Pi Coding Agent, and DeepSeek Harness; user authorized committing the completed branch.

## Next Action
- Push the committed feature branch only if explicitly requested.

## Blockers
- None.

## Last Check
- Ran: Pre-commit full suite: 286 tests passed with 12 expected Windows POSIX skips; content, memory, sync, and diff checks passed.
- Boundary: Locally verified on Windows; Command Code and DeepSeek live installation remain CI-only until the branch is pushed and CI runs.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Push the committed feature branch only if explicitly requested.
