---
format: "forge-memory-v1"
mission_id: "publish-forge-0.4.0"
state: "ready"
checkpointed_at: null
---
# Current Mission

## Outcome
- Statement: Publish Forge 0.4.0 with the Claude Code mission guard after the feature passes GitHub CI.

## Scope
- In: Feature branch and PR, Core CI, merge to main, release preparation, v0.4.0 tag, push, GitHub Release, publication verification, and the local plugin switch to the published artifact.
- Out: Unrelated product changes, automated deployment, bypassing required checks, and publishing a build that has not passed CI.
- Constraints: Follow `scripts/release.sh` and its allowlist/receipt protocol; release only from a clean synchronized main branch after Core CI passes; do not add attribution trailers.

## Success Criteria
- [ ] The guard feature and its tests are committed and pushed on a feature branch.
- [ ] Core CI passes on the pull request and on main after merge.
- [ ] `scripts/release.sh prepare 0.4.0` produces exactly the six-file version diff.
- [ ] `scripts/release.sh commit 0.4.0 --authorized` creates `release(forge): v0.4.0` and tag `v0.4.0`.
- [ ] The release commit and tag are pushed, and Core CI passes on the release commit.
- [ ] A non-draft, non-prerelease GitHub Release for `v0.4.0` is verified.
- [ ] The published `forge@forge` 0.4.0 install is verified, and the local `forge-local` copy is disabled or removed.
- [ ] `.forge/MISSION.md` records the release and validates.

## Latest Delivery
- None yet; this Mission was just activated.

## Next Action
- Revert the six version files to 0.3.0, commit the guard feature with the 0.4.0 changelog entry, and push the feature branch.

## Blockers
- None.

## Last Check
- Ran: none; Mission activation only.
- Boundary: no feature commit, release commit, tag, or push yet.

## Resume
- Read: `.forge/INTENT.md`, `.forge/MISSION.md`, `VERSION`, `scripts/release.sh`.
- Do: commit the feature, open the PR, and proceed through the release protocol.
