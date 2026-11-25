---
format: "forge-memory-v1"
mission_id: "publish-forge-0.4.0"
state: "done"
checkpointed_at: "2026-10-29T01:38:26Z"
---
# Current Mission

## Outcome
- Statement: Publish Forge 0.4.0 with the Claude Code mission guard after the feature passes GitHub CI.

## Scope
- In: Feature branch and PR, Core CI, merge to main, release preparation, v0.4.0 tag, push, GitHub Release, publication verification, and the local plugin switch to the published artifact.
- Out: Unrelated product changes, automated deployment, bypassing required checks, and publishing a build that has not passed CI.
- Constraints: Follow `scripts/release.sh` and its allowlist/receipt protocol; release only from a clean synchronized main branch after Core CI passes; do not add attribution trailers.

## Success Criteria
- [x] The guard feature and its tests are committed and pushed on a feature branch.
- [x] Core CI passes on the pull request and on main after merge.
- [x] `scripts/release.sh prepare 0.4.0` produces exactly the six-file version diff.
- [x] `scripts/release.sh commit 0.4.0 --authorized` creates `release(forge): v0.4.0` and tag `v0.4.0`.
- [x] The release commit and tag are pushed, and Core CI passes on the release commit.
- [x] A non-draft, non-prerelease GitHub Release for `v0.4.0` is verified.
- [x] The published `forge@forge` 0.4.0 install is verified, and the local `forge-local` copy is disabled or removed.
- [x] `.forge/MISSION.md` records the release and validates.

## Latest Delivery
- Published v0.4.0: PR #4 merged, all 9 Core CI jobs green on the PR, main, and release commit, six-file release commit e4f446f and tag v0.4.0 pushed, GitHub Release verified, and the published forge@forge 0.4.0 installed locally with forge-local removed.

## Next Action
- None; the Mission is complete. A future Mission needs explicit user confirmation.

## Blockers
- None.

## Last Check
- Ran: 9/9 Core CI jobs passed on PR #4, main d457642, and release e4f446f; forge-memory-validate and the installed-guard smoke test passed.
- Boundary: Verified the tag SHA, published archive, installed plugin validation, and direct guard behavior; a host restart is required to load the new hook in an active session.

## Resume
- Read: `.forge/INTENT.md`, `.forge/MISSION.md`, `VERSION`, `scripts/release.sh`.
- Do: None; the Mission is complete. A future Mission needs explicit user confirmation.
