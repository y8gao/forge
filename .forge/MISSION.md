---
format: "forge-memory-v1"
mission_id: "ci-release-platform-boundary"
state: "working"
checkpointed_at: "2026-09-05T10:36:19Z"
---
# Current Mission

## Outcome
- Statement: Run executable `release.sh` workflow tests on Linux while retaining Windows validation for the cross-platform Python product surface.

## Scope
- In: Encode the POSIX-only release execution boundary, keep static release checks cross-platform, synchronize both repositories, verify, commit, push, and inspect CI.
- Out: Change release semantics, install WSL, remove the Windows matrix, or modify host compatibility jobs.
- Constraints: Keep Linux coverage for every release workflow case and Windows coverage for the remaining Python product surface.

## Success Criteria
- [x] A regression test encodes that executable `release.sh` workflow cases are POSIX-only.
- [x] Linux continues to run every release workflow case through the full suite.
- [x] Windows continues to validate static release contracts and the cross-platform Python product surface.
- [x] Both repositories retain synchronized workflows and regression tests.
- [ ] Local checks pass and the fix is committed and pushed to both `main` branches.
- [ ] The resulting public Core CI run is inspected and its exact status reported.

## Latest Delivery
- Encoded the POSIX-only release execution boundary, removed the ineffective Git Bash shell override, and retained the Windows matrix for all remaining product tests.

## Next Action
- Commit and push the corrected boundary to both repositories, then inspect the resulting public Core CI run.

## Blockers
- None.

## Last Check
- Ran: Both repositories: actionlint v1.7.12, content validation, memory validation, git diff check, and full 278-test Windows suite PASS with 12 expected skips.
- Boundary: Local Windows verification confirms executable release workflow tests are skipped; Linux and hosted Windows confirmation require the next CI run.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Commit and push the corrected boundary to both repositories, then inspect the resulting public Core CI run.
