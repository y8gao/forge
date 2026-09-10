---
format: "forge-memory-v1"
mission_id: "publish-forge-0.3.0"
state: "working"
checkpointed_at: "2026-09-10T07:52:47Z"
---
# Current Mission

## Outcome
- Statement: Publish Forge 0.3.0 after the public-interface change passes GitHub CI.

## Scope
- In: Interactive Cursor visibility evidence, feature commit and push, pull-request CI, integration to main, release preparation, v0.3.0 tag push, GitHub Release, and publication verification.
- Out: Unrelated product changes, automated deployment, or bypassing required GitHub checks.
- Constraints: Follow scripts/release.sh and its allowlist/receipt protocol; release only from a clean synchronized main branch after required CI passes.

## Success Criteria
- [ ] The four-public/five-internal Cursor visibility result is recorded in committed control memory.
- [ ] The feature commit is pushed and its required GitHub CI checks pass.
- [ ] The public-interface change is integrated into main without bypassing required checks.
- [ ] release.sh prepares and commits exactly the allowed 0.3.0 version files and creates v0.3.0.
- [ ] The release commit and tag are pushed and a non-draft, non-prerelease GitHub Release is verified.

## Latest Delivery
- PR #3 merged the CI-verified public-interface change into main; Core CI run 34451871437 then passed all nine jobs on merge commit f1049e2.

## Next Action
- Commit the 0.3.0 changelog and Mission checkpoint, then run the two-phase release.sh protocol from clean synchronized main.

## Blockers
- None.

## Last Check
- Ran: PR #3 checks passed; merge commit f1049e2 was pushed to main; Core CI run 34451871437 completed successfully with nine passing jobs.
- Boundary: The product change is ci_verified; 0.3.0 version files, release commit, tag, push, GitHub Release, and post-publication verification remain pending.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Commit the 0.3.0 changelog and Mission checkpoint, then run the two-phase release.sh protocol from clean synchronized main.
