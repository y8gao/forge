---
format: "forge-memory-v1"
mission_id: "forge-0.4.0-install"
state: "done"
checkpointed_at: "2026-10-29T00:49:34Z"
---
# Current Mission

## Outcome
- Statement: Ship Forge 0.4.0 with the Claude Code mission guard, synchronize every version manifest and the changelog, and install the workspace checkout as the active Claude Code plugin.

## Scope
- In: `VERSION`, root `package.json`, the three plugin manifests, the DeepSeek Harness package, `CHANGELOG.md`, local marketplace/install commands, and install-path verification.
- Out: git commit, push, GitHub release, public marketplace publication, and unrelated plugin changes.
- Constraints: Keep all version values synchronized; install from `/Users/gaoyang/Workspace/forge`; keep the public `forge` GitHub marketplace recoverable; a restart is required before the hook is live.

## Success Criteria
- [x] All six version values equal 0.4.0.
- [x] `CHANGELOG.md` has a dated 0.4.0 entry containing the guard.
- [x] `python3 scripts/validate-content.py` passes.
- [x] `claude plugin validate plugins/forge` passes.
- [x] `claude plugin list` shows enabled Forge 0.4.0 from the local checkout.
- [x] The installed plugin contains `hooks/hooks.json` and `scripts/forge-guard`, and simulated PreToolUse calls block `done` and allow `ready`.
- [x] No new test failures beyond the six pre-existing `test_release` failures on macOS bash 3.2.

## Latest Delivery
- Forge 0.4.0 is versioned and installed as forge@forge-local at user scope; the old forge@forge 0.3.0 installs are disabled; the installed cache contains the PreToolUse guard, with done=2 and ready=0 simulations.

## Next Action
- Restart Claude Code so the newly installed plugin hooks load; the current session is not guarded yet.

## Blockers
- None.

## Last Check
- Ran: validate-content PASS; 13 guard tests PASS; full suite 339 tests with 6 pre-existing mapfile failures and 3 skipped; claude plugin validate passed with only the icon warning; installed guard simulation done=2 ready=0; plugin details reports Hooks (1) PreToolUse.
- Boundary: No live post-install session yet, so hook activation is unverified until restart. No commit, push, release, or public marketplace publication. The local marketplace holds a copy of plugins/forge; refresh and reinstall it after future plugin edits.

## Resume
- Read: `.forge/INTENT.md`, `.forge/MISSION.md`, `VERSION`.
- Do: Restart Claude Code so the newly installed plugin hooks load; the current session is not guarded yet.
