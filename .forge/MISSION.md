---
format: "forge-memory-v1"
mission_id: "ci-windows-bash-fix"
state: "working"
checkpointed_at: "2026-09-05T10:24:28Z"
---
# Current Mission

## Outcome
- Statement: Make the release workflow tests use Git for Windows Bash in the GitHub Actions Windows matrix instead of the WSL launcher.

## Scope
- In: Add a regression contract, update the Core CI full-suite shell, synchronize both repositories, verify, commit, push, and inspect the resulting CI run.
- Out: Change release semantics, install WSL, weaken the Windows matrix, or modify host compatibility jobs.
- Constraints: Keep the fix workflow-local and minimal; preserve the existing cross-platform test matrix and least-privilege boundary.

## Success Criteria
- [x] A regression test requires the full-suite CI step to run with Git Bash.
- [ ] Windows Python 3.11 and 3.14 no longer resolve `bash` to the WSL launcher.
- [x] Both repositories retain synchronized workflows and regression tests.
- [ ] Local checks pass and the fix is committed and pushed to both `main` branches.
- [ ] The resulting public Core CI run is inspected and its exact status reported.

## Latest Delivery
- Added synchronized regression coverage and configured the Core CI full-suite step to run under Git for Windows Bash.

## Next Action
- Commit and push the fix to both repositories, then inspect the resulting Windows Python 3.11 and 3.14 CI jobs.

## Blockers
- None.

## Last Check
- Ran: Both repositories: actionlint v1.7.12 PASS; content and memory validation PASS; explicit Git Bash full suite 277 PASS with 1 Windows POSIX-mode skip; git diff check PASS.
- Boundary: Locally verified with the same Git Bash executable class used by GitHub Actions; hosted Windows CI confirmation is pending publication.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: Commit and push the fix to both repositories, then inspect the resulting Windows Python 3.11 and 3.14 CI jobs.
