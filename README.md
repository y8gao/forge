# Forge

Keep coding agents aligned across sessions without adding another runtime.

Forge saves active direction in two small, human-reviewable Markdown files:
`.forge/INTENT.md` for durable project intent and `.forge/MISSION.md` for the
current outcome, boundaries, progress, and next action.

## Why Forge

- **Resume from intent, not chat history.** Each session starts from concise,
  project-owned memory instead of reconstructing context from old transcripts.
- **Direct by default.** Ordinary work stays lightweight and is handled by the
  host agent without a mandatory workflow.
- **Extra control only when asked.** Bounded Loop and independent Assurance are
  explicit opt-ins for work that needs iteration or stronger checking.
- **Focused capabilities, not a simulated team.** Scout, Builder, and Checker
  are temporary task profiles rather than permanent roles or a fixed pipeline.
- **Native across three hosts.** Claude Code, Codex, and Cursor share the same
  Memory-First semantics through thin native packages.
- **No runtime to operate.** Forge is a content package with Markdown memory and
  small local helpers—no daemon, scheduler, database, or lock service.

## How it works

1. Ask the agent to initialize Forge in the project.
2. Describe the outcome you want in ordinary language.
3. Forge reads active intent, does the work directly, and records only meaningful
   decisions, deliveries, pauses, completions, or Mission replacements.
4. A later session reads the same two files and continues from the saved next action.

Only the host agent writes active control memory. Commit, push, publish, deploy,
and other external effects still require specific authorization.

## First-class hosts

- Claude Code: native plugin in `plugins/forge/.claude-plugin/plugin.json`
- Codex: native plugin in `plugins/forge/.codex-plugin/plugin.json`
- Cursor: native plugin in `plugins/forge/.cursor-plugin/plugin.json`

All three packages expose the same shared skills and exactly three capability
profiles: `forge-scout`, `forge-builder`, and `forge-checker`. Host wrappers
contain only native metadata, permissions, and references to shared contracts.
GitHub Copilot and VS Code are not first-class Forge product hosts.

## Install

### Claude Code

```text
/plugin marketplace add https://github.com/y8gao/forge
/plugin install forge@forge
```

### Codex

```text
codex plugin marketplace add .agents/plugins/marketplace.json
codex plugin install forge
```

### Cursor

Add this repository's `.cursor-plugin/marketplace.json` through Cursor's plugin
marketplace, then install `forge`. The package explicitly declares shared
skills, a Cursor orientation rule, and the three native agents. Skills are the
only slash-invokable Forge entrypoints, avoiding duplicate command names.

Install through the native Claude Code, Codex, or Cursor package surface and
initialize projects directly with Memory-First control memory.

## Use

In Claude Code, Codex, or Cursor, describe the outcome you want in ordinary
language:

- For ordinary work, Forge reads the saved project direction, restates the
  outcome, and handles the task directly.
- For bounded continuation, ask Forge to continue for at most 3 iterations,
  showing each useful delta and stopping at the bound.
- For an independent report-only check, ask for a fresh independent check with
  no repairs.
- For authorized bounded repair, Forge repairs only the accepted scope and
  then requires a fresh independent check.
- To pause, ask Forge to save exactly where to continue; later, ask it to resume
  that work.
- For an external effect, authorize the specific external action and target,
  such as committing this worktree or publishing a named release.

Aliases are optional convenience entrypoints; natural-language requests are
the shared interaction across hosts. This package describes shared contracts
and packaging, but does not claim live all-host behavior has been exercised.
Only the host agent writes active control memory, and historical material
under `.forge/archive/` is not loaded by default.

## Validate

```sh
python -m unittest tests.test_platform_agents tests.test_cursor_package \
  tests.test_release tests.test_release_receipt
python scripts/validate-content.py
git diff --check
```

## Versioning

The canonical version is `VERSION`. Release preparation synchronizes it with
the Claude Code, Codex, and Cursor plugin manifests. Release tooling is local
and two-phase; it does not publish automatically:

```sh
scripts/release.sh prepare <version>
scripts/release.sh commit <version> --authorized
```

`prepare` does not commit or tag. `commit` requires explicit authorization.
Push and publication remain separate user actions.

## License

MIT — see [LICENSE](./LICENSE).
