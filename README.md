# Forge

[![Core CI](https://github.com/y8gao/forge/actions/workflows/ci.yml/badge.svg)](https://github.com/y8gao/forge/actions/workflows/ci.yml)

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
- **Native profile parity on three hosts.** Claude Code, Codex, and Cursor use
  thin native packages with host-enforced Scout, Builder, and Checker wrappers.
- **Portable Core on three more.** Command Code, Pi, and DeepSeek Harness load
  the same nine Memory-First skills through their standard package mechanisms.
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
- Command Code: standard Agent Skills from `.agents/skills`
- Pi Coding Agent: Pi package declared by the root `package.json`
- DeepSeek Harness: experimental DSH bundle in `packages/deepseek-harness`

All six hosts receive the same nine skills. Claude Code, Codex, and Cursor also
provide native wrappers for `forge-scout`, `forge-builder`, and
`forge-checker`. Command Code, Pi, and DeepSeek Harness have Core-level support.
Forge does not guarantee Scout/Builder/Checker permission isolation on those
hosts, although the profile skills remain available.

## Install

### Claude Code

```text
/plugin marketplace add https://github.com/y8gao/forge
/plugin install forge@forge
```

### Codex

```text
codex plugin marketplace add y8gao/forge --ref main
codex plugin add forge@forge
```

### Cursor

Add this repository's `.cursor-plugin/marketplace.json` through Cursor's plugin
marketplace, then install `forge`. The package explicitly declares shared
skills, a Cursor orientation rule, and the three native agents. Skills are the
only slash-invokable Forge entrypoints, avoiding duplicate command names.

### Command Code

Command Code 1.49.1 or newer requires Node.js 22. Install the repository's
standard Agent Skills and select all nine Forge skills:

```sh
command-code skills add y8gao/forge
```

On native Windows, the shorter CLI alias is `cmdc`; `command-code` works on all
platforms.

### Pi Coding Agent

With Pi Coding Agent 0.85.1 or newer on Node.js 22.19 or newer, install the Git
package; Pi reads `pi.skills` from the root package manifest:

```sh
pi install git:github.com/y8gao/forge@main
```

### DeepSeek Harness

DeepSeek Harness support is experimental and pinned to `0.1.2-rc.1` on Node.js
22.19 or newer. From a Forge checkout, install the bundle into the desired DSH
profile:

```sh
dsh plugin --profile default add ./packages/deepseek-harness
```

The bundle registers all nine packaged skills with skill-local resource bases.
It can be installed as `forge-memory-first-dsh` after that package is published;
this repository does not publish automatically.

## Use

In Claude Code, Codex, Cursor, Command Code, Pi, or DeepSeek Harness, describe
the outcome you want in ordinary language:

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
  tests.test_portable_hosts \
  tests.test_release tests.test_release_receipt
python scripts/validate-content.py
git diff --check
```

Core CI runs the full suite and validators on Ubuntu and Windows. Pull requests
also run package checks with fixed CLI versions. They cover Claude Code, Codex,
Command Code, Pi, and the experimental DeepSeek Harness bundle. A weekly Host
Compatibility workflow repeats those checks with the latest CLIs and verifies
available public Git or marketplace paths.

Cursor manifests, component paths, and native agents are covered by blocking
static contract tests. Cursor does not currently expose a supported headless
installer, so CI does not claim a live Cursor installation test.
DeepSeek Harness public npm installation remains unchecked until
`forge-memory-first-dsh` is published; CI composes the package from checkout.

## Versioning

The canonical version is `VERSION`. Release preparation synchronizes it with
the Claude Code, Codex, and Cursor plugin manifests plus the Pi and DeepSeek
Harness package manifests. Release tooling is local and two-phase; it does not
publish automatically:

```sh
scripts/release.sh prepare <version>
scripts/release.sh commit <version> --authorized
```

`prepare` does not commit or tag. `commit` requires explicit authorization.
Push and publication remain separate user actions.

## License

MIT — see [LICENSE](./LICENSE).
