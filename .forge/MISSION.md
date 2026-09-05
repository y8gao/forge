---
format: "forge-memory-v1"
mission_id: "ci-release-platform-boundary"
state: "done"
checkpointed_at: "2026-09-05T10:38:42Z"
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
- [x] Local checks pass and the fix is committed and pushed to both `main` branches.
- [x] The resulting public Core CI run is inspected and its exact status reported.

## Latest Delivery
- Published the POSIX-only release execution boundary while preserving Windows product coverage; corrected Core CI passed in both repositories.

## Next Action
- Address the Node.js 20 deprecation annotations by updating pinned GitHub Actions in a separate maintenance change.

## Blockers
- None.

## Last Check
- Ran: Public Core CI run 33961133482 PASS: Ubuntu Python 3.11/3.14, Windows Python 3.11/3.14, Claude install, and Codex install all succeeded; private run 33961129864 also PASS.
- Boundary: CI-verified for the corrected test boundary; GitHub reports non-blocking Node.js 20 deprecation annotations for the pinned Actions.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Address the Node.js 20 deprecation annotations by updating pinned GitHub Actions in a separate maintenance change.
