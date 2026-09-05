---
format: "forge-memory-v1"
mission_id: "release-0.1.0"
state: "done"
checkpointed_at: "2026-09-05T07:30:07Z"
---
# Current Mission

## Outcome
- Statement: Publish the first Forge Memory-First 0.1.0 release from a clean public repository with no private exploration commit history.

## Scope
- In: Finalize the private source, archive the old private `forge` runtime repo, audit a history-free product snapshot, create public `y8gao/forge`, and publish its first 0.1.0 release.
- Out: Publish any exploration repository or history, merge unrelated repositories, expose secrets, or modify `forge-app` and `forge-pi`.
- Constraints: Public Git starts from a fresh initial commit with no transplanted refs; preserve the private source history; follow the two-phase release workflow.

## Success Criteria
- [x] CHANGELOG contains a dated first-public-release 0.1.0 entry and no exploration-era release entries.
- [x] `forge-status` renders deterministic Mission, Progress, and Verification Markdown groups with regression coverage.
- [x] README leads with Forge's distinctive value, explains the minimum workflow and boundaries clearly, and remains concise.
- [x] Active control memory and templates use the first-public `forge-memory-v1` schema with no compatibility layer.
- [x] The committed pre-release baseline is 0.0.0 across VERSION and all host manifests.
- [x] A current-product snapshot passes secret and historical-surface audits without any source `.git` history.
- [x] The old private `y8gao/forge` is renamed and archived without publishing its runtime history.
- [x] Public `y8gao/forge` starts from the audited snapshot as one clean initial commit.
- [x] `release.sh prepare 0.1.0` passes and changes only the four version allowlist files.
- [x] The prepared diff and sealed release receipt are reviewed.
- [x] The authorized release commit, `v0.1.0` tag, push, and public GitHub Release complete successfully.

## Latest Delivery
- Published Forge Memory-First 0.1.0 from a clean public repository with no private exploration Git history; archived the old runtime repository and preserved private source history separately.

## Next Action
- Collect first-release feedback and open a new Mission for any follow-up product change.

## Blockers
- None.

## Last Check
- Ran: Full source suite 273 PASS with 1 Windows POSIX-mode skip; fresh installed v1 smoke PASS; release prepare and commit gates each passed 97 packaging/content tests plus 17 release workflow tests; sealed receipt valid; public main and v0.1.0 pushed; GitHub Release created.
- Boundary: Locally verified and publicly published; Claude and Codex CLIs were unavailable for live native-host validation, and no CI workflow or global host marketplace submission was run.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Collect first-release feedback and open a new Mission for any follow-up product change.
