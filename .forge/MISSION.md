---
format: "forge-memory-v1"
mission_id: "release-forge-0.2.0"
state: "ready"
checkpointed_at: null
---
# Current Mission

## Outcome
- Statement: Publish Forge version 0.2.0 from the verified main branch.

## Scope
- In: Changelog finalization, release preparation checks, synchronized version manifests, release commit, v0.2.0 tag, push, GitHub Release, and post-publication verification.
- Out: Additional product changes, dependency upgrades, automated deployment, or unrelated repository cleanup.
- Constraints: Follow scripts/release.sh and its allowlist/receipt protocol; preserve existing release history; stop on any failed check.

## Success Criteria
- [ ] Changelog contains a committed 0.2.0 entry and the preparation branch is clean and synchronized.
- [ ] release.sh prepares and validates exactly the six allowed version files for 0.2.0.
- [ ] The release commit and v0.2.0 tag are pushed and their CI evidence is reported honestly.
- [ ] A non-draft, non-prerelease GitHub Release for v0.2.0 is published and verified.

## Latest Delivery
- User authorized publishing Forge v0.2.0.

## Next Action
- Finalize and commit the 0.2.0 Changelog entry.

## Blockers
- None.

## Last Check
- Ran: Confirmed main matched origin/main, v0.2.0 was absent, v0.1.0 remained latest, and Core CI passed for the reliability commit.
- Boundary: Changelog, version manifests, release receipt, tag, and GitHub Release have not been created.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Finalize and commit the 0.2.0 Changelog entry.
