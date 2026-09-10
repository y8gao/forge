---
format: "forge-memory-v1"
mission_id: "publish-forge-0.3.0"
state: "done"
checkpointed_at: "2026-09-10T08:48:10Z"
---
# Current Mission

## Outcome
- Statement: Publish Forge 0.3.0 after the public-interface change passes GitHub CI.

## Scope
- In: Interactive Cursor visibility evidence, feature commit and push, pull-request CI, integration to main, release preparation, v0.3.0 tag push, GitHub Release, and publication verification.
- Out: Unrelated product changes, automated deployment, or bypassing required GitHub checks.
- Constraints: Follow scripts/release.sh and its allowlist/receipt protocol; release only from a clean synchronized main branch after required CI passes.

## Success Criteria
- [x] The four-public/five-internal Cursor visibility result is recorded in committed control memory.
- [x] The feature commit is pushed and its required GitHub CI checks pass.
- [x] The public-interface change is integrated into main without bypassing required checks.
- [x] release.sh prepares and commits exactly the allowed 0.3.0 version files and creates v0.3.0.
- [x] The release commit and tag are pushed and a non-draft, non-prerelease GitHub Release is verified.

## Latest Delivery
- Published Forge v0.3.0 with the simplified four-entrypoint public interface, synchronized version manifests, release commit 52c8158, passing Core CI, and a verified public GitHub Release.

## Next Action
- Await user direction for the next Forge Mission.

## Blockers
- None.

## Last Check
- Ran: release.sh prepare and commit checks passed; release commit 52c8158 and v0.3.0 match origin; Core CI run 34456339275 succeeded; gh release view confirms Forge 0.3.0 is published, non-draft, and non-prerelease; all six version values equal 0.3.0.
- Boundary: ci_verified for configured Core CI and release protocol; live Cursor CLI visibility was manually verified locally; Claude and Codex CLIs were unavailable during local release checks, so their pinned CI installation gates provide host evidence. No automated deployment beyond the GitHub Release was performed.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Await user direction for the next Forge Mission.
