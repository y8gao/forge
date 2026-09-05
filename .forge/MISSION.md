---
format: "forge-memory-v1"
mission_id: "ci-automation"
state: "done"
checkpointed_at: "2026-09-05T08:32:41Z"
---
# Current Mission

## Outcome
- Statement: Add two-tier GitHub Actions automation that continuously validates Forge and exercises supported host installation paths honestly.

## Scope
- In: Synchronize core CI and host compatibility workflows across private source and public repositories; add fixed-version Claude/Codex install gates, latest-version monitoring, Cursor static contract checks, documentation, and regression coverage.
- Out: Commit, push, branch-protection changes, CI deployment, global marketplace submission, or unsupported claims of headless Cursor installation.
- Constraints: Use least-privilege Actions pinned by immutable SHA; isolate host configuration; require no API keys; keep fixed PR gates separate from latest compatibility monitoring.

## Success Criteria
- [x] Core CI runs validation and the full suite on Ubuntu and Windows for supported Python versions.
- [x] Pull requests use fixed Claude Code and Codex CLI versions for isolated local marketplace installation smoke tests.
- [x] A scheduled/manual workflow exercises latest Claude Code and Codex compatibility and the public marketplace path.
- [x] Cursor coverage stays explicit and static until a supported headless installer exists.
- [x] Workflows use least privilege, immutable Action revisions, concurrency cancellation, and bounded timeouts.
- [x] README, CHANGELOG, and regression tests document and enforce the two-tier boundary.
- [x] Both repositories pass proportional local verification with synchronized CI product files.

## Latest Delivery
- Added synchronized two-tier GitHub Actions, pinned Claude Code and Codex PR installation gates, latest compatibility monitoring, Cursor static boundaries, documentation, and regression contracts.

## Next Action
- After explicit commit and push authorization, publish both workflow sets, observe real GitHub Actions results, and configure required checks.

## Blockers
- None.

## Last Check
- Ran: Both repositories: full 277-test suite PASS with 1 Windows POSIX-mode skip; 14 targeted tests PASS; content and memory validation PASS; bash syntax, git diff check, actionlint v1.7.12, and synchronized-file comparison PASS.
- Boundary: Locally verified only; no real GitHub Actions run, live host CLI installation, commit, push, or branch-protection change was performed.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md` only.
- Do: After explicit commit and push authorization, publish both workflow sets, observe real GitHub Actions results, and configure required checks.
