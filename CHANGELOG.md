# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

### Added
- Added cross-platform core CI, pinned Claude Code and Codex installation gates,
  and scheduled latest-host compatibility monitoring.

### Fixed
- Corrected the Codex installation instructions for the public Git marketplace.
- Forced the cross-platform CI suite to use Git Bash so Windows runners do not
  invoke the WSL launcher.

## [0.1.0] - 2026-09-05

### Added
- Memory-First Core over canonical `.forge/INTENT.md` and `.forge/MISSION.md`
- Explicit bounded Loop and opt-in claim-scoped Assurance
- Temporary Scout, Builder, and Checker capability profiles
- Thin native Claude Code, Codex, and Cursor wrappers over shared profiles
- Cursor plugin manifest, marketplace, skill entrypoints, and orientation rule
- Deterministic initialization, checkpoint, compaction, validation, and grouped Markdown status helpers
- Exact Mission state tokens with helper-based `done` completion and mandatory post-write validation
- Static three-host packaging, content, release, and sealed receipt checks
