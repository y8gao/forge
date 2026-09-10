---
format: "forge-memory-v1"
mission_id: "verify-current-cursor-skill-visibility"
state: "done"
checkpointed_at: "2026-09-10T03:40:14Z"
---
# Current Mission

## Outcome
- Statement: Update Cursor Agent and verify the four-public/five-internal Forge skill visibility contract on the current CLI.

## Scope
- In: Authorized Cursor Agent update, version confirmation, local-plugin read-only slash probes, and exact evidence reporting.
- Out: Forge product changes, IDE or Cloud testing, other host testing, commits, pushes, or workarounds for Cursor runtime behavior.
- Constraints: Load the current branch through `--plugin-dir`; use Ask mode and no repository write authority; distinguish documented metadata from observed CLI behavior.

## Success Criteria
- [x] Cursor Agent is updated and its resulting version is recorded.
- [x] A public Forge skill resolves through the local plugin.
- [x] An internal `user-invocable: false` skill is tested for typed slash rejection.
- [x] Repository state remains free of unexpected product changes and the live result is reported honestly.

## Latest Delivery
- Updated Cursor Agent to 2026.09.08-6caf4ff and completed public, internal, inventory, and non-TTY slash probes against the local Forge plugin.

## Next Action
- Manually inspect the interactive /skills palette in a TTY if deterministic menu-visibility evidence is required, or authorize committing the feature branch.

## Blockers
- None.

## Last Check
- Ran: agent update completed; agent --version returned 2026.09.08-6caf4ff; /forge-status loaded the public skill; /forge-core returned Core content; headless /skills generated a model answer; piped interactive startup exited because non-TTY execution forced print mode; repository status showed no unexpected probe-created product files.
- Boundary: Headless output cannot distinguish typed slash resolution from automatic model invocation for user-invocable false skills, and no machine-readable skill inventory exists; actual interactive menu hiding remains unverified.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Manually inspect the interactive /skills palette in a TTY if deterministic menu-visibility evidence is required, or authorize committing the feature branch.
