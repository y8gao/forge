---
format: "forge-memory-v1"
mission_id: "fix-new-host-ci"
state: "working"
checkpointed_at: "2026-09-07T02:14:12Z"
---
# Current Mission

## Outcome
- Statement: Fix the GitHub Actions failures introduced by the new coding-agent host support.

## Scope
- In: Diagnose workflow validation and host installation failures, add regression coverage, fix workflows, verify locally, commit, push, and inspect resulting CI.
- Out: Change host support tiers, publish npm packages, or add unrelated maintenance.
- Constraints: Preserve least-privilege permissions, pinned PR gates, latest-version monitoring, and honest verification boundaries.

## Success Criteria
- [ ] Both workflow files pass GitHub-aware semantic validation.
- [ ] Core CI creates jobs and all required checks pass.
- [ ] Host Compatibility creates the intended scheduled/manual jobs without running on ordinary pushes.
- [ ] The fix is covered by regression tests and pushed to the feature branch.

## Latest Delivery
- GitHub created all intended jobs; every job passed except the two DSH local-bundle jobs, whose logs showed pnpm missing. Added pinned pnpm setup and regression coverage.

## Next Action
- Commit and push the pnpm fix, then rerun both workflows.

## Blockers
- None.

## Last Check
- Ran: 13 platform tests passed; actionlint 1.7.7 passed both workflows; git diff --check passed.
- Boundary: DSH repair is locally verified but has not yet run on GitHub.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Commit and push the pnpm fix, then rerun both workflows.
