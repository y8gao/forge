---
format: "forge-memory-v1"
mission_id: "publish-forge-0.3.0"
state: "working"
checkpointed_at: "2026-09-10T07:42:49Z"
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
- Cursor Agent 2026.09.08-6caf4ff interactively showed only forge-init, forge-status, forge-loop, and forge-assurance under /forge-; three separate subagent profiles remained visible as designed.

## Next Action
- Review the complete feature diff, commit it, push the feature branch, and open a pull request to trigger Core CI.

## Blockers
- None.

## Last Check
- Ran: Manual /forge- autocomplete showed four public Forge skills; 326 unit tests passed with 12 skipped; validate-content, sync-portable-skills, and forge-memory-validate passed.
- Boundary: Local verification is complete; GitHub CI, main integration, release preparation, tag publication, and GitHub Release remain pending.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Review the complete feature diff, commit it, push the feature branch, and open a pull request to trigger Core CI.
