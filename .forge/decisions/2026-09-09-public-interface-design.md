# Forge Public Interface Simplification

**Date:** 2026-09-09  
**Baseline:** Forge v0.2.0  
**Status:** Approved design, pending implementation

## Outcome

Forge presents natural language as its default interaction and exposes only four
explicit user entrypoints:

- `forge-init`
- `forge-status`
- `forge-loop`
- `forge-assurance`

The other five packaged skills remain available to the host as internal
capabilities, not advertised user commands:

- `forge-core`
- `forge-memory`
- `forge-scout`
- `forge-builder`
- `forge-checker`

The six executable memory helpers remain internal control protocols and are not
part of the advertised conversational command surface.

## Architecture

All nine skills remain in the existing canonical `plugins/forge/skills`
payload. Forge does not create a second skill tree, runtime loader, capability
registry, or routing layer.

Invocation metadata defines the interface boundary:

- The four public skills explicitly set `user-invocable: true`.
- `forge-loop` and `forge-assurance` also disable automatic model invocation
  where supported because both modes require an explicit user request.
- The five internal skills set `user-invocable: false` and remain eligible for
  model invocation. They must not set `disable-model-invocation: true`.
- Codex-specific metadata disables implicit invocation for Loop and Assurance
  without changing their explicit availability.

The existing native Scout, Builder, and Checker agent definitions remain
packaged for Cursor, Claude Code, and Codex. Agent-picker visibility is separate
from the slash-command surface and is not changed by this work.

## Documentation

README usage is reorganized around three concepts:

1. Describe ordinary work in natural language.
2. Use the four public entrypoints only when explicit control is useful.
3. Treat Core, Memory, and temporary profiles as advanced host capabilities.

The helper scripts are documented as internal implementation protocols. Their
names and direct invocation examples may remain in maintainer or validation
documentation, but they are not presented as normal end-user commands.

Claims must distinguish product intent from host guarantees. Cursor CLI
documents `user-invocable: false`; Cursor IDE and Cloud do not provide the same
explicit guarantee. Claude Code documents the field but has reported extension
visibility defects. Codex uses skill references rather than a slash list and
does not provide an equivalent user-visibility field.

## Synchronization

Canonical skill metadata is the source of truth. The portable synchronization
script propagates the same public/internal classification to `.agents` and the
DeepSeek Harness bundle. Host-specific sidecars remain adjacent to the skill
they configure and are included only where the host recognizes them.

Synchronization must not fork skill bodies or create host-specific copies of
Core semantics.

## Failure Handling

- Unknown metadata may be ignored by a host; this must not prevent skill
  loading.
- If a host displays an internal skill despite the metadata, documentation must
  report the limitation instead of claiming universal hiding.
- A synchronization mismatch is a contract-test failure.
- Public-interface changes must not modify active-memory schemas or helper
  behavior.

## Verification

Implementation follows test-first development:

1. Add failing contracts that assert exactly four canonical public skills and
   five model-available internal skills.
2. Add failing synchronization contracts for portable payloads.
3. Add failing documentation contracts for the public, advanced, and internal
   hierarchy.
4. Apply the minimum metadata and documentation changes.
5. Run targeted package, content, portable-host, and skill contract tests.
6. Run the full local suite after targeted checks pass.

Where practical, inspect the installed Cursor CLI skill list. IDE, Cloud,
Claude, Codex, Command Code, Pi, and DeepSeek behavior not exercised directly
must remain an explicit verification boundary.

## Non-goals

- Removing any of the nine skills.
- Removing native profile agents.
- Adding commands, wrappers, runtime hooks, routers, registries, or loaders.
- Changing INTENT/MISSION schemas or helper semantics.
- Claiming identical command-menu behavior across hosts.
